#!/usr/bin/env python3
"""
Test AgentCore Gateway MCP Endpoint

Obtains a JWT token from Cognito using client credentials flow,
then calls the gateway's /mcp endpoint to list available tools.

Reference: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-using-mcp-call.html
"""

import json
import requests
import base64
from typing import Dict, Any

def load_cognito_config(filename: str = 'cognito_config.json') -> Dict[str, Any]:
    """
    Load Cognito configuration from JSON file.
    
    Args:
        filename: Configuration file path
        
    Returns:
        Dict: Cognito configuration
    """
    with open(filename, 'r') as f:
        return json.load(f)


def load_gateway_config(filename: str = 'AgentCoreProject/agentcore/.cli/deployed-state.json') -> str:
    """
    Load gateway URL from deployed state.
    
    Args:
        filename: Deployed state file path
        
    Returns:
        str: Gateway URL
    """
    with open(filename, 'r') as f:
        state = json.load(f)
    
    return state['targets']['default']['resources']['mcp']['gateways']['workshop-gateway']['gatewayUrl']


def obtain_jwt_token(cognito_config: Dict[str, Any]) -> str:
    """
    Obtain a JWT access token from Cognito using client credentials flow.
    
    The client credentials grant is used for machine-to-machine authentication.
    Reference: https://docs.aws.amazon.com/cognito/latest/developerguide/token-endpoint.html
    
    Args:
        cognito_config: Cognito configuration with client_id, client_secret, etc.
        
    Returns:
        str: JWT access token
    """
    print("🔐 Obtaining JWT token from Cognito...")
    print(f"   Token Endpoint: {cognito_config['token_endpoint']}")
    
    # Prepare Basic Authentication header
    # Format: Basic base64(client_id:client_secret)
    credentials = f"{cognito_config['client_id']}:{cognito_config['client_secret']}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    # Request access token using client_credentials grant
    response = requests.post(
        cognito_config['token_endpoint'],
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': f'Basic {encoded_credentials}'
        },
        data={
            'grant_type': 'client_credentials',
            'scope': cognito_config['scope']
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to obtain token: {response.status_code}")
        print(f"   Response: {response.text}")
        raise Exception(f"Token request failed: {response.text}")
    
    token_data = response.json()
    access_token = token_data['access_token']
    expires_in = token_data.get('expires_in', 'unknown')
    
    print(f"✅ Token obtained successfully")
    print(f"   Token type: {token_data.get('token_type', 'Bearer')}")
    print(f"   Expires in: {expires_in} seconds")
    print(f"   Scope: {token_data.get('scope', cognito_config['scope'])}")
    
    return access_token


def list_gateway_tools(gateway_url: str, access_token: str) -> Dict[str, Any]:
    """
    Call the gateway's MCP endpoint to list available tools.
    
    Uses the MCP protocol's tools/list operation.
    Reference: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-using-mcp-list.html
    
    Args:
        gateway_url: The gateway MCP endpoint URL
        access_token: JWT access token for authorization
        
    Returns:
        Dict: MCP response with list of tools
    """
    print(f"\n🔧 Listing tools from gateway...")
    print(f"   Gateway URL: {gateway_url}")
    
    # MCP tools/list request using JSON-RPC 2.0 format
    # The gateway URL already includes /mcp, so we just POST to it
    response = requests.post(
        gateway_url,
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        },
        json={
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/list',
            'params': {}
        }
    )
    
    if response.status_code != 200:
        print(f"❌ Failed to list tools: {response.status_code}")
        print(f"   Response: {response.text}")
        raise Exception(f"Tools list request failed: {response.text}")
    
    return response.json()


def display_tools(tools_response: Dict[str, Any]):
    """
    Display the tools returned by the gateway.
    
    Args:
        tools_response: MCP response containing tools
    """
    print("\n" + "=" * 80)
    print("✅ Gateway Tools")
    print("=" * 80)
    
    tools = tools_response.get('result', {}).get('tools', [])
    
    if not tools:
        print("⚠️  No tools found")
        return
    
    print(f"\nFound {len(tools)} tools:\n")
    
    for i, tool in enumerate(tools, 1):
        print(f"{i}. {tool['name']}")
        print(f"   Description: {tool.get('description', 'No description')}")
        
        # Display input schema
        input_schema = tool.get('inputSchema', {})
        if input_schema:
            properties = input_schema.get('properties', {})
            required = input_schema.get('required', [])
            
            if properties:
                print(f"   Parameters:")
                for param_name, param_info in properties.items():
                    param_type = param_info.get('type', 'unknown')
                    param_desc = param_info.get('description', '')
                    required_marker = ' (required)' if param_name in required else ''
                    print(f"     - {param_name}: {param_type}{required_marker}")
                    if param_desc:
                        print(f"       {param_desc}")
        
        print()


def main():
    """
    Main test function.
    """
    print("=" * 80)
    print("🚀 AgentCore Gateway MCP Endpoint Test")
    print("=" * 80)
    print()
    
    try:
        # Load configurations
        cognito_config = load_cognito_config()
        gateway_url = load_gateway_config()
        
        print(f"📋 Configuration loaded:")
        print(f"   User Pool: {cognito_config['user_pool_id']}")
        print(f"   Client ID: {cognito_config['client_id']}")
        print(f"   Scope: {cognito_config['scope']}")
        print(f"   Gateway: {gateway_url}")
        print()
        
        # Step 1: Obtain JWT token
        access_token = obtain_jwt_token(cognito_config)
        
        # Step 2: List tools from gateway
        tools_response = list_gateway_tools(gateway_url, access_token)
        
        # Step 3: Display tools
        display_tools(tools_response)
        
        # Save full response for inspection
        with open('gateway_tools_response.json', 'w') as f:
            json.dump(tools_response, f, indent=2)
        
        print("💾 Full response saved to gateway_tools_response.json")
        print()
        
    except FileNotFoundError as e:
        print(f"\n❌ Configuration file not found: {e}")
        print("   Make sure cognito_config.json exists and gateway is deployed")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise


if __name__ == '__main__':
    main()
