from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from app.services.query_expander import query_expander
from app.services.retriever import retriever_service
from app.services.generator import generator_service
import asyncpg

class AgentState(TypedDict):
    raw_query: str
    expanded_query: str
    retrieved_data: Dict[str, Any]
    final_output: str
    execution_provider: str
    db_conn: asyncpg.Connection
    chat_history: List[Dict[str, str]]

async def expand_query_node(state: AgentState) -> Dict[str, Any]:
    expanded = await query_expander.expand_query(state["raw_query"])
    return {"expanded_query": expanded}

async def retrieve_standards_node(state: AgentState) -> Dict[str, Any]:
    conn = state["db_conn"]
    data = await retriever_service.search_standards(conn, state["expanded_query"])
    return {"retrieved_data": data}

async def generate_synthesis_node(state: AgentState) -> Dict[str, Any]:
    output, provider = await generator_service.generate_response(
        state["raw_query"], 
        state["retrieved_data"],
        state["chat_history"]
    )
    return {"final_output": output, "execution_provider": provider}

def build_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)

    workflow.add_node("expand_query", expand_query_node)
    workflow.add_node("retrieve_standards", retrieve_standards_node)
    workflow.add_node("generate_synthesis", generate_synthesis_node)

    workflow.set_entry_point("expand_query")
    workflow.add_edge("expand_query", "retrieve_standards")
    workflow.add_edge("retrieve_standards", "generate_synthesis")
    workflow.add_edge("generate_synthesis", END)

    return workflow.compile()

agent_executor = build_workflow()