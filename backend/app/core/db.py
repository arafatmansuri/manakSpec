import psycopg2
from pgvector.psycopg2 import register_vector
from app.core.config import settings

def get_db_connection():
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        register_vector(conn)
        return conn
    except Exception as e:
        print(f"Error connecting to PostgreSQL database: {e}")
        raise e