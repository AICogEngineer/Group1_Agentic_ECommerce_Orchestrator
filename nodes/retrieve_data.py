"""
retrieve_data.py

Node: retrieve_data

Purpose:
- Retrieve user order and account data from internal data sources using credentials from .env
- Combine multi-source outputs into a structured format
- Store results in AgentState.retrieved for downstream processing
"""

import os
from typing import Any
from agent.state import AgentState, AgentStatus, RetrievalOutputs

# Example database / API clients (replace with real implementations)
    # Credentials are read from environment variables
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")


def fetch_order_from_snowflake(user_id: str, order_id: str) -> dict:
    """
    Fetch order data for a user from Snowflake.
    Replace this stub with a real Snowflake query using SNOWFLAKE_USER / PASSWORD / ACCOUNT.
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


def retrieve_data_node(state: AgentState) -> str:
    """
    Retrieves structured data for the user request using credentials from .env.

    Steps:
    1. Extract user_id and order_id from AgentState
    2. Use Snowflake credentials to fetch order data
    3. Retrieve policy context
    4. Populate AgentState.retrieved
    5. Update state.status to DATA_RETRIEVED

    Args:
        state: Current AgentState object

    Returns:
        str: Next step identifier for the graph routing
    """

    # Pull identifiers from state or .env
    user_id = state.user_id or os.getenv("USER_ID")
    order_id = state.order_id

    if not user_id:
        raise ValueError("USER_ID must be set in state or .env for data retrieval")

    # Fetch order data from Snowflake (replace with real query)
    order_data = fetch_order_from_snowflake(user_id, order_id)

    # Fetch policy context
    policy_context = fetch_policy_context(order_data)

    # Populate AgentState.retrieved with typed outputs
    state.retrieved = RetrievalOutputs(
        order_data = order_data,
        policy_context = policy_context
    )

    # Update lifecycle status using enum
    state.status = AgentStatus.DATA_RETRIEVED

    # Routing: continue to fraud/red-flag checker
    return "continue"
