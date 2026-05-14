from strands import Agent
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from model.load import load_model
from strands_tools import current_time
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
import requests
import base64
import threading

# Import AgentCore Memory components
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig, RetrievalConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

app = BedrockAgentCoreApp()
log = app.logger

# OAuth Token Manager for Gateway Authentication
class OAuthTokenManager:
    """
    Manages OAuth 2.0 client credentials token lifecycle for gateway authentication.
    
    Handles token acquisition, caching, and automatic refresh before expiry.
    Thread-safe implementation for concurrent access.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        token_endpoint: str,
        scope: str
    ):
        """
        Initialize the OAuth token manager.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            token_endpoint: Token endpoint URL
            scope: OAuth scope for gateway access
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_endpoint = token_endpoint
        self.scope = scope
        
        # Token cache
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._lock = threading.Lock()
        
        log.info(f"OAuth Token Manager initialized for scope: {scope}")
    
    def get_access_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            str: Valid JWT access token
        """
        with self._lock:
            # Check if we have a valid cached token
            if self._access_token and self._token_expiry:
                # Refresh token 5 minutes before expiry
                if datetime.now() < self._token_expiry - timedelta(minutes=5):
                    log.debug("Using cached access token")
                    return self._access_token
            
            # Token expired or not cached, obtain new token
            log.info("Obtaining new access token from Cognito")
            return self._obtain_new_token()
    
    def _obtain_new_token(self) -> str:
        """
        Obtain a new access token using client credentials flow.
        
        Reference: https://docs.aws.amazon.com/cognito/latest/developerguide/token-endpoint.html
        
        Returns:
            str: New JWT access token
        """
        try:
            # Prepare Basic Authentication header
            # Format: Basic base64(client_id:client_secret)
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            # Request access token using client_credentials grant
            response = requests.post(
                self.token_endpoint,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Authorization': f'Basic {encoded_credentials}'
                },
                data={
                    'grant_type': 'client_credentials',
                    'scope': self.scope
                },
                timeout=10
            )
            
            if response.status_code != 200:
                log.error(f"Failed to obtain token: {response.status_code} - {response.text}")
                raise Exception(f"Token request failed: {response.text}")
            
            token_data = response.json()
            self._access_token = token_data['access_token']
            
            # Calculate token expiry (default to 3600 seconds if not provided)
            expires_in = token_data.get('expires_in', 3600)
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
            
            log.info(f"Access token obtained successfully, expires in {expires_in} seconds")
            return self._access_token
            
        except Exception as e:
            log.error(f"Error obtaining access token: {str(e)}")
            raise


# Global token manager instance
_token_manager: Optional[OAuthTokenManager] = None

def get_token_manager() -> OAuthTokenManager:
    """
    Get or create the global OAuth token manager.
    
    Returns:
        OAuthTokenManager: Token manager instance
    """
    global _token_manager
    
    if _token_manager is None:
        # Read OAuth configuration from environment variables
        client_id = os.environ.get("GATEWAY_CLIENT_ID")
        client_secret = os.environ.get("GATEWAY_CLIENT_SECRET")
        token_endpoint = os.environ.get("GATEWAY_TOKEN_ENDPOINT")
        scope = os.environ.get("GATEWAY_SCOPE")
        
        if not all([client_id, client_secret, token_endpoint, scope]):
            raise ValueError(
                "Missing required OAuth configuration. "
                "Ensure GATEWAY_CLIENT_ID, GATEWAY_CLIENT_SECRET, "
                "GATEWAY_TOKEN_ENDPOINT, and GATEWAY_SCOPE are set."
            )
        
        _token_manager = OAuthTokenManager(
            client_id=client_id,
            client_secret=client_secret,
            token_endpoint=token_endpoint,
            scope=scope
        )
    
    return _token_manager


def create_gateway_mcp_transport():
    """
    Create an MCP transport for the AgentCore Gateway with OAuth authentication.
    
    The transport handles HTTP communication with the gateway, including
    automatic OAuth token management and authorization headers.
    
    Reference: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-agent-integration.html
    
    Returns:
        Streamable HTTP transport configured for gateway access
    """
    gateway_url = os.environ.get("GATEWAY_URL")
    
    if not gateway_url:
        raise ValueError("GATEWAY_URL environment variable not set")
    
    log.info(f"Creating MCP transport for gateway: {gateway_url}")
    
    # Get OAuth token manager
    token_manager = get_token_manager()
    
    # Obtain access token
    access_token = token_manager.get_access_token()
    
    # Create transport with Authorization header
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    return streamablehttp_client(gateway_url, headers=headers)


# Global MCP client instance
_mcp_client: Optional[MCPClient] = None

def get_mcp_client() -> MCPClient:
    """
    Get or create the global MCP client for gateway access.
    
    Returns:
        MCPClient: MCP client instance
    """
    global _mcp_client
    
    if _mcp_client is None:
        log.info("Initializing MCP client for AgentCore Gateway")
        _mcp_client = MCPClient(create_gateway_mcp_transport)
    
    return _mcp_client


# Global agent instance
_agent = None

def get_or_create_agent():
    """
    Get or create the global agent instance.
    
    The agent is configured with:
    - Bedrock model for inference
    - Memory integration for conversation context
    - Gateway tools via MCP client
    - Built-in tools (current_time)
    
    Returns:
        Agent: Configured agent instance
    """
    global _agent
    
    if _agent is None:
        log.info("Creating agent with gateway tools")
        
        # Get memory configuration from environment variables
        memory_id = os.environ.get("AGENTCORE_MEMORY_ID")
        aws_region = os.environ.get("AWS_REGION", "us-west-2")
        
        # Default actor_id to "administrator" as specified
        actor_id = "administrator"
        
        # Generate a unique session ID for this conversation
        session_id = f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Configure memory with retrieval settings for each namespace
        agentcore_memory_config = AgentCoreMemoryConfig(
            memory_id=memory_id,
            session_id=session_id,
            actor_id=actor_id,
            retrieval_config={
                # User preferences namespace
                f"/users/{actor_id}/preferences": RetrievalConfig(
                    top_k=5,
                    relevance_score=0.7
                ),
                # Semantic facts namespace
                f"/users/{actor_id}/facts": RetrievalConfig(
                    top_k=10,
                    relevance_score=0.5
                ),
                # Summarization namespace
                f"/summaries/{actor_id}/{session_id}": RetrievalConfig(
                    top_k=5,
                    relevance_score=0.6
                ),
                # Episodic memory namespace
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
        
        # Get MCP client and load gateway tools
        mcp_client = get_mcp_client()
        
        # Start MCP client - it will remain active for the lifetime of the agent
        mcp_client.start()
        gateway_tools = mcp_client.list_tools_sync()
        log.info(f"Loaded {len(gateway_tools)} tools from gateway")
        
        # Combine gateway tools with built-in tools
        all_tools = [current_time] + gateway_tools
        
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
                
                Available tools:
                - current_time: Get current date and time
                - order_lookup: Look up order details from DynamoDB
                - user_lookup: Retrieve customer information
                - product_lookup: Retrieve product information
                - policy_retrieval: Query return policies from knowledge base
            """,
            tools=all_tools,
            session_manager=session_manager
        )
        
        log.info("Agent created successfully with gateway integration")
    
    return _agent


@app.entrypoint
async def invoke(payload, context):
    """
    Agent invocation entrypoint.
    
    Processes incoming requests and streams responses back to the caller.
    
    Args:
        payload: Request payload containing the prompt
        context: Invocation context
    """
    log.info("Invoking Agent with gateway tools")

    agent = get_or_create_agent()

    # Execute and format response
    stream = agent.stream_async(payload.get("prompt"))

    async for event in stream:
        # Handle Text parts of the response
        if "data" in event and isinstance(event["data"], str):
            yield event["data"]


if __name__ == "__main__":
    app.run()
