from strands import Agent, tool
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from model.load import load_model
from mcp_client.client import get_streamable_http_mcp_client
from strands_tools import current_time
from datetime import datetime, timedelta
from typing import Optional
import os

# Import AgentCore Memory components
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

app = BedrockAgentCoreApp()
log = app.logger

# Define a Streamable HTTP MCP Client
mcp_clients = [get_streamable_http_mcp_client()]

# Define a collection of tools used by the model
tools = []

# Add built-in current_time tool from strands_tools
tools.append(current_time)

# Mock data for orders, users, and products
MOCK_ORDERS = {
    "ORD-001": {
        "order_id": "ORD-001",
        "customer_id": "C-01",
        "product_id": "P-001",
        "product_name": "iPhone 15 Pro",
        "status": "DELIVERED",
        "order_date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
        "delivery_date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
        "price": 999.99
    },
    "ORD-002": {
        "order_id": "ORD-002",
        "customer_id": "C-02",
        "product_id": "P-002",
        "product_name": "Kindle Paperwhite",
        "status": "DELIVERED",
        "order_date": (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"),
        "delivery_date": (datetime.now() - timedelta(days=42)).strftime("%Y-%m-%d"),
        "price": 139.99
    },
    "ORD-003": {
        "order_id": "ORD-003",
        "customer_id": "C-01",
        "product_id": "P-005",
        "product_name": "PlayStation 5",
        "status": "SHIPPED",
        "order_date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
        "delivery_date": None,
        "price": 499.99
    }
}

MOCK_USERS = {
    "C-01": {
        "user_id": "C-01",
        "name": "Rajesh Kumar",
        "country": "IN",
        "email": "rajesh@example.com"
    },
    "C-02": {
        "user_id": "C-02",
        "name": "Sarah Johnson",
        "country": "US",
        "email": "sarah@example.com"
    },
    "C-03": {
        "user_id": "C-03",
        "name": "James Wilson",
        "country": "UK",
        "email": "james@example.com"
    }
}

MOCK_PRODUCTS = {
    "P-001": {
        "product_id": "P-001",
        "name": "iPhone 15 Pro",
        "manufacturer": "Apple",
        "category": "phone"
    },
    "P-002": {
        "product_id": "P-002",
        "name": "Kindle Paperwhite",
        "manufacturer": "Amazon",
        "category": "e-book"
    },
    "P-003": {
        "product_id": "P-003",
        "name": "iPad Air",
        "manufacturer": "Apple",
        "category": "tablet"
    },
    "P-005": {
        "product_id": "P-005",
        "name": "PlayStation 5",
        "manufacturer": "Sony",
        "category": "electronics"
    }
}

MOCK_POLICIES = {
    "electronics": {
        "category": "electronics",
        "return_window_days": 30,
        "refund_percentage": 100,
        "conditions": "100% refund if unopened, 85% refund if opened (15% restocking fee)",
        "notes": "Must include original packaging and accessories"
    },
    "clothing": {
        "category": "clothing",
        "return_window_days": 60,
        "refund_percentage": 100,
        "conditions": "Full refund with tags attached and unworn",
        "notes": "Free return shipping"
    },
    "books": {
        "category": "books",
        "return_window_days": 14,
        "refund_percentage": 50,
        "conditions": "50% refund for opened books, 100% for unopened",
        "notes": "Digital books are non-returnable"
    }
}

@tool
def order_lookup(order_id: str) -> str:
    """
    Look up order details by order ID.
    
    Args:
        order_id: The unique order identifier (e.g., ORD-001)
        
    Returns:
        str: Formatted order details including customer, product, status, and dates
    """
    order = MOCK_ORDERS.get(order_id)
    
    if not order:
        return f"Order {order_id} not found in the system."
    
    # Format the order details
    result = f"""Order Details:
- Order ID: {order['order_id']}
- Customer ID: {order['customer_id']}
- Product: {order['product_name']} (ID: {order['product_id']})
- Status: {order['status']}
- Order Date: {order['order_date']}
- Delivery Date: {order['delivery_date'] if order['delivery_date'] else 'Not yet delivered'}
- Price: ${order['price']:.2f}"""
    
    return result

tools.append(order_lookup)

@tool
def user_lookup(user_id: str) -> str:
    """
    Retrieve customer information by user ID.
    
    Args:
        user_id: The unique customer identifier (e.g., C-01)
        
    Returns:
        str: Formatted customer details including name, country, and email
    """
    user = MOCK_USERS.get(user_id)
    
    if not user:
        return f"Customer {user_id} not found in the system."
    
    # Format the customer details
    result = f"""Customer Details:
- Customer ID: {user['user_id']}
- Name: {user['name']}
- Country: {user['country']}
- Email: {user['email']}"""
    
    return result

tools.append(user_lookup)

@tool
def product_lookup(product_id: str) -> str:
    """
    Retrieve product information by product ID.
    
    Args:
        product_id: The unique product identifier (e.g., P-001)
        
    Returns:
        str: Formatted product details including name, manufacturer, and category
    """
    product = MOCK_PRODUCTS.get(product_id)
    
    if not product:
        return f"Product {product_id} not found in the system."
    
    # Format the product details
    result = f"""Product Details:
- Product ID: {product['product_id']}
- Name: {product['name']}
- Manufacturer: {product['manufacturer']}
- Category: {product['category']}"""
    
    return result

tools.append(product_lookup)

@tool
def policy_retrieval(query: str) -> str:
    """
    Retrieve return policy information for a product category.
    
    Args:
        query: The product category to look up (e.g., electronics, clothing, books)
        
    Returns:
        str: Formatted return policy details for the specified category
    """
    # Normalize the query to lowercase for matching
    category = query.lower().strip()
    
    policy = MOCK_POLICIES.get(category)
    
    if not policy:
        # Return all available policies if specific category not found
        available = ", ".join(MOCK_POLICIES.keys())
        return f"Policy for '{query}' not found. Available categories: {available}"
    
    # Format the policy details
    result = f"""Return Policy for {policy['category'].title()}:
- Return Window: {policy['return_window_days']} days from delivery
- Refund: {policy['conditions']}
- Additional Notes: {policy['notes']}"""
    
    return result

tools.append(policy_retrieval)

# Add MCP client to tools if available
for mcp_client in mcp_clients:
    if mcp_client:
        tools.append(mcp_client)


_agent = None

def get_or_create_agent():
    global _agent
    if _agent is None:
        # Get memory configuration from environment variables
        memory_id = os.environ.get("AGENTCORE_MEMORY_ID")
        aws_region = os.environ.get("AWS_REGION", "us-west-2")
        
        # Default actor_id to "administrator" as specified
        actor_id = "administrator"
        
        # Generate a unique session ID for this conversation
        session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Configure memory with retrieval settings for each namespace
        # Using the exact namespace patterns from agentcore.json
        agentcore_memory_config = AgentCoreMemoryConfig(
            memory_id=memory_id,
            session_id=session_id,
            actor_id=actor_id,
            retrieval_config={
                # User preferences namespace - retrieve user-specific preferences
                f"/users/{actor_id}/preferences": RetrievalConfig(
                    top_k=5,
                    relevance_score=0.7
                ),
                # Semantic facts namespace - retrieve factual information about the user
                f"/users/{actor_id}/facts": RetrievalConfig(
                    top_k=10,
                    relevance_score=0.5
                ),
                # Summarization namespace - retrieve session summaries
                f"/summaries/{actor_id}/{session_id}": RetrievalConfig(
                    top_k=5,
                    relevance_score=0.6
                ),
                # Episodic memory namespace - retrieve episodic memories
                f"/episodes/{actor_id}/{session_id}": RetrievalConfig(
                    top_k=8,
                    relevance_score=0.5
                )
            }
        )
        
        # Create session manager with memory configuration
        session_manager = AgentCoreMemorySessionManager(
            agentcore_memory_config=agentcore_memory_config,
            region_name=aws_region
        )
        
        _agent = Agent(
            model=load_model(),
            system_prompt="""
                You are a Returns & Refunds Assistant helping administrators manage customer returns and refunds.
                
                Your role:
                - Assist administrators who have access to customer data, orders, and return policies
                - Help check return eligibility based on order dates, product conditions, and company policies
                - Calculate refund amounts according to return policies (restocking fees, shipping costs, etc.)
                - Answer questions about return policies and procedures on behalf of customers
                - Provide clear guidance on return authorization, shipping labels, and refund timelines
                
                Guidelines:
                - Be helpful, professional, and concise in your responses
                - Always confirm order details and eligibility criteria before processing returns or refunds
                - Clearly explain policy rules (30-day return window, condition requirements, etc.)
                - Ask for clarification when order information is incomplete or ambiguous
                - Use available tools to look up order data, calculate refunds, and check policies
                - Escalate complex cases or policy exceptions to human supervisors when appropriate
                - Remember user preferences and past interactions to provide personalized assistance
            """,
            tools=tools,
            session_manager=session_manager
        )
    return _agent


@app.entrypoint
async def invoke(payload, context):
    log.info("Invoking Agent.....")

    agent = get_or_create_agent()

    # Execute and format response
    stream = agent.stream_async(payload.get("prompt"))

    async for event in stream:
        # Handle Text parts of the response
        if "data" in event and isinstance(event["data"], str):
            yield event["data"]


if __name__ == "__main__":
    app.run()
