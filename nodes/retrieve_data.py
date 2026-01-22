"""
retrieve_data.py

Node: retrieve_data

Purpose:
- Retrieve user order and account data from internal data sources (Snowflake + Pinecone)
- Combine multi-source outputs into a structured format
- Store results in AgentState.retrieved for downstream processing
- Fully compatible with LangSmith tracing
"""

import os
from typing import Any
from agent.state import AgentState, AgentStatus, RetrievalOutputs

import pinecone
from openai import OpenAI

# Example database / API clients (replace with real implementations)
    # Credentials are read from environment variables
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "orders-index")  # default index

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def fetch_order_from_snowflake(user_id: str, order_id: str) -> dict:
    """
    Fetch order data for a user from Snowflake
    Replace this stub with a real Snowflake query using credentials from .env
    """
    # Example mock response
    return {
        "order_id": order_id or "ORD12345",
        "user_id": user_id,
        "items": [
            {"sku": "SKU001", "name": "Wireless Mouse", "quantity": 1},
            {"sku": "SKU002", "name": "Keyboard", "quantity": 1}
        ],
        "total": 120.50,
        "status": "shipped"
    }


def fetch_policy_context(order_data: dict) -> dict:
    """
    Fetch relevant policy context for the order.
    Could be fetched from a database or config service.
    """
    return {
        "return_window_days": 30,
        "refund_policy": "Full refund within 30 days of delivery",
        "shipping_guarantee": "2-day shipping guaranteed"
    }

# Pinecone retrieval helper
def fetch_order_from_pinecone(query: str) -> dict:
    """
    Query Pinecone index for order-related data using embeddings.
    Returns top result metadata.
    """
    # Initialize Pinecone if not already
    if not pinecone.is_initialized():
        pinecone.init(api_key = PINECONE_API_KEY, environment = PINECONE_ENV)

    # Connect to index
    index = pinecone.Index(PINECONE_INDEX_NAME)

    # Create embedding for query
    client = OpenAI(api_key = OPENAI_API_KEY)
    embedding_resp = client.embeddings.create(
        model = "text-embedding-3-small",
        input = query
    )
    vector = embedding_resp["data"][0]["embedding"]

    # Query Pinecone index
    result = index.query(vector = vector, top_k = 1, include_metadata = True) # top k controls how many results to return
    if result.matches:
        return result.matches[0].metadata or {}
    
    return {}

def retrieve_data_node(state: AgentState) -> str:
    """
    Retrieves structured order and policy data from Snowflake and Pinecone,
    populates AgentState.retrieved, and updates status to DATA_RETRIEVED.

    Args:
        state: Current AgentState object

    Returns:
        str: Next step identifier for graph routing
    """

    # Pull identifiers from state or .env
    user_id = state.user_id or os.getenv("USER_ID")
    order_id = state.order_id

    if not user_id:
        raise ValueError("USER_ID must be set in state or .env for data retrieval")

    # Snowflake fetch
    order_data = fetch_order_from_snowflake(user_id, order_id)

    # Policy context fetch
    policy_context = fetch_policy_context(order_data)

    # Pinecone augmentation
    pinecone_data = fetch_order_from_pinecone(state.user_input)

    # Merge Pinecone data into order_data
    if pinecone_data:
        order_data.update(pinecone_data) # simple merge for demo

    # Populate AgentState.retrieved with typed outputs
    state.retrieved = RetrievalOutputs(
        order_data = order_data,
        policy_context = policy_context
    )

    # Update lifecycle status
    state.status = AgentStatus.DATA_RETRIEVED

    # Routing: continue to fraud/red-flag checker
    return "continue"
