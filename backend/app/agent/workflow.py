import json
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from app.services.query_expander import query_expander
from app.services.retriever import retriever_service
from app.services.generator import generator_service
from app.core.config import settings
from google import genai
from google.genai import types
import asyncpg

# DB similarity score below this triggers a supplementary web search
WEB_SEARCH_SIMILARITY_THRESHOLD = 0.60


class AgentState(TypedDict):
    raw_query: str
    expanded_query: str
    detected_language: str
    target_language: str
    english_query: str
    retrieved_data: Dict[str, Any]
    final_output: Any
    execution_provider: str
    db_conn: asyncpg.Connection
    chat_history: List[Dict[str, str]]


async def expand_query_node(state: AgentState) -> Dict[str, Any]:
    expansion = await query_expander.expand_query(state["raw_query"], state.get("target_language"))
    return {
        "expanded_query": expansion["expanded_query"],
        "detected_language": expansion.get("detected_language", "English"),
        "english_query": expansion.get("english_translation", state["raw_query"]),
    }


async def retrieve_standards_node(state: AgentState) -> Dict[str, Any]:
    conn = state["db_conn"]
    data = await retriever_service.search_standards(conn, state["expanded_query"])
    return {"retrieved_data": data}


def _should_web_search(state: AgentState) -> str:
    """Route to web_search when DB confidence is low, otherwise go straight to synthesis."""
    max_score = state.get("retrieved_data", {}).get("max_similarity_score", 0.0)
    db_standards = state.get("retrieved_data", {}).get("primary_standards", [])
    if not db_standards or max_score < WEB_SEARCH_SIMILARITY_THRESHOLD:
        return "web_search"
    return "generate"


async def web_search_node(state: AgentState) -> Dict[str, Any]:
    """
    Uses Gemini with Google Search grounding to find relevant BIS/IS standards
    when DB retrieval confidence is low or returns no results.

    Discovered standards are stored under `web_standards` in retrieved_data.
    This key is purely internal — the generator uses it to populate
    primary_standards_summary in the final response.
    """
    query = state.get("english_query") or state["raw_query"]
    search_prompt = (
        f"Find all relevant Bureau of Indian Standards (BIS) / Indian Standards (IS) "
        f"that are applicable to the following procurement or product query: {query}. "
        f"For each standard found, return a JSON array where each object has these keys: "
        f"is_number (e.g. IS 1234:2020), title, publication_year (integer or null), "
        f"status (Active or Withdrawn), scope_text (brief applicability summary), "
        f"is_mandatory_qco (true/false), scheme_type (e.g. Scheme-I, CRS, or null). "
        f"Return ONLY the JSON array, no other text."
    )

    web_standards: List[Dict[str, Any]] = []
    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.PRIMARY_LLM_MODEL,
            contents=search_prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.2,
            ),
        )
        raw = response.text or ""

        # Extract JSON array — may be wrapped in markdown fences
        start = raw.find("[")
        end = raw.rfind("]")
        if start != -1 and end != -1 and end > start:
            parsed = json.loads(raw[start: end + 1])
            if isinstance(parsed, list):
                for item in parsed:
                    if not item.get("is_number"):
                        continue  # skip malformed entries
                    web_standards.append({
                        "is_number": item.get("is_number", ""),
                        "title": item.get("title", ""),
                        "publication_year": item.get("publication_year"),
                        "status": item.get("status", "Active"),
                        "scope_text": item.get("scope_text", ""),
                        "is_mandatory_qco": bool(item.get("is_mandatory_qco", False)),
                        "scheme_type": item.get("scheme_type"),
                        "similarity_score": 0.0,
                        "technical_specifications": {},
                    })

    except Exception as e:
        # Non-fatal: synthesis proceeds with only DB results (or empty)
        print(f"[web_search_node] Web search failed (non-fatal): {e}")

    # Attach web_standards to retrieved_data without overwriting DB results
    updated = dict(state.get("retrieved_data", {}))
    updated["web_standards"] = web_standards
    return {"retrieved_data": updated}


async def generate_synthesis_node(state: AgentState) -> Dict[str, Any]:
    output_lang = state.get("target_language") or state.get("detected_language") or "English"
    output, provider = await generator_service.generate_response(
        state["raw_query"],
        state["retrieved_data"],
        state["chat_history"],
        target_language=output_lang,
    )
    return {"final_output": output, "execution_provider": provider}


def build_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("expand_query", expand_query_node)
    workflow.add_node("retrieve_standards", retrieve_standards_node)
    workflow.add_node("web_search", web_search_node)
    workflow.add_node("generate_synthesis", generate_synthesis_node)

    workflow.set_entry_point("expand_query")
    workflow.add_edge("expand_query", "retrieve_standards")

    # Conditional: low DB confidence → web search first; high confidence → synthesise directly
    workflow.add_conditional_edges(
        "retrieve_standards",
        _should_web_search,
        {
            "web_search": "web_search",
            "generate": "generate_synthesis",
        },
    )

    workflow.add_edge("web_search", "generate_synthesis")
    workflow.add_edge("generate_synthesis", END)

    return workflow.compile()


agent_executor = build_workflow()