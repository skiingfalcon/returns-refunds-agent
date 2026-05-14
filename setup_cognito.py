#!/usr/bin/env python3
"""
Setup Cognito User Pool for AgentCore Gateway Authentication

Creates a Cognito User Pool configured for machine-to-machine (M2M) authentication
using OAuth 2.0 client credentials flow.

Reference: https://docs.aws.amazon.com/cognito/latest/developerguide/federation-endpoints-oauth-grants.html
"""

import boto3
import json
import time
from typing import Dict, Any

# Initialize AWS clients with us-west-2 region as per project standards
cognito = boto3.client('cognito-idp', region_name='us-west-2')

def create_user_pool() -> Dict[str, Any]:
    """
    Create a Cognito User Pool for gateway authentication.
    
    Returns:
        Dict: User pool details including ID and ARN
    """
    print("📦 Creating Cognito User Pool: workshop-gateway-auth")
    
    response = cognito.create_user_pool(
        PoolName='workshop-gateway-auth',
        # Minimal configuration for M2M authentication
        # No password policies needed since this is for client credentials only
        AutoVerifiedAttributes=[],
        # Enable OAuth 2.0 flows
        UserPoolAddOns={
            'AdvancedSecurityMode': 'OFF'  # Keep costs minimal for workshop
        }
    )
    
    user_pool = response['UserPool']
    user_pool_id = user_pool['Id']
    
    print(f"✅ User Pool created: {user_pool_id}")
    return {
        'user_pool_id': user_pool_id,
        'arn': user_pool['Arn']
    }


def create_user_pool_domain(user_pool_id: str) -> str:
    """
    Create a domain prefix for OAuth endpoints.
    
    The domain enables the OAuth 2.0 token endpoint for client credentials flow.
    
    Args:
        user_pool_id: The Cognito User Pool ID
        
    Returns:
        str: The domain prefix
    """
    # Generate a unique domain prefix using timestamp
    domain_prefix = f"workshop-gateway-{int(time.time())}"
    
    print(f"🌐 Creating User Pool domain: {domain_prefix}")
    
    try:
        cognito.create_user_pool_domain(
            Domain=domain_prefix,
            UserPoolId=user_pool_id
        )
        print(f"✅ Domain created: {domain_prefix}.auth.us-west-2.amazoncognito.com")
        return domain_prefix
    except cognito.exceptions.InvalidParameterException as e:
        print(f"⚠️  Domain creation failed: {e}")
        # If domain exists, try with a different suffix
        domain_prefix = f"workshop-gw-{int(time.time())}"
        cognito.create_user_pool_domain(
            Domain=domain_prefix,
            UserPoolId=user_pool_id
        )
        print(f"✅ Domain created: {domain_prefix}.auth.us-west-2.amazoncognito.com")
        return domain_prefix


def create_resource_server(user_pool_id: str) -> Dict[str, Any]:
    """
    Create a resource server with custom scopes for gateway invocation.
    
    Resource servers define the protected resources and their scopes.
    The custom scope will be used to authorize gateway tool invocations.
    
    Args:
        user_pool_id: The Cognito User Pool ID
        
    Returns:
        Dict: Resource server details including identifier and scopes
    """
    print("🔐 Creating resource server with custom scope")
    
    # Resource server identifier (typically a URI)
    resource_server_identifier = 'gateway-api'
    
    response = cognito.create_resource_server(
        UserPoolId=user_pool_id,
        Identifier=resource_server_identifier,
        Name='GatewayAPI',
        Scopes=[
            {
                'ScopeName': 'invoke',
                'ScopeDescription': 'Permission to invoke gateway tools'
            }
        ]
    )
    
    resource_server = response['ResourceServer']
    full_scope = f"{resource_server_identifier}/invoke"
    
    print(f"✅ Resource server created: {resource_server_identifier}")
    print(f"   Scope: {full_scope}")
    
    return {
        'identifier': resource_server_identifier,
        'scope': full_scope
    }


def create_app_client(user_pool_id: str, resource_scope: str) -> Dict[str, Any]:
    """
    Create an app client configured for machine-to-machine (client_credentials) flow.
    
    This app client will be used by the gateway to authenticate API requests.
    
    Args:
        user_pool_id: The Cognito User Pool ID
        resource_scope: The full scope string (e.g., 'gateway-api/invoke')
        
    Returns:
        Dict: App client details including client_id and client_secret
    """
    print("🔑 Creating app client for M2M authentication")
    
    response = cognito.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName='gateway-m2m-client',
        # Generate a client secret (required for client credentials flow)
        GenerateSecret=True,
        # Token validity periods
        AccessTokenValidity=60,  # 60 minutes
        TokenValidityUnits={
            'AccessToken': 'minutes'
        },
        # Enable ONLY client credentials grant
        # Cannot mix client_credentials with authorization_code or implicit
        AllowedOAuthFlows=['client_credentials'],
        AllowedOAuthFlowsUserPoolClient=True,
        # Specify the custom scope for gateway invocation
        AllowedOAuthScopes=[resource_scope],
        # Prevent user authentication flows
        ExplicitAuthFlows=[],
        # No callback URLs needed for M2M
        CallbackURLs=[],
        LogoutURLs=[]
    )
    
    client = response['UserPoolClient']
    client_id = client['ClientId']
    
    # Retrieve the client secret (only available immediately after creation)
    describe_response = cognito.describe_user_pool_client(
        UserPoolId=user_pool_id,
        ClientId=client_id
    )
    
    client_secret = describe_response['UserPoolClient']['ClientSecret']
    
    print(f"✅ App client created: {client_id}")
    print(f"   Client credentials flow enabled")
    print(f"   Scope: {resource_scope}")
    
    return {
        'client_id': client_id,
        'client_secret': client_secret
    }


def save_config(config: Dict[str, Any], filename: str = 'cognito_config.json'):
    """
    Save Cognito configuration to a JSON file.
    
    Args:
        config: Configuration dictionary
        filename: Output filename
    """
    print(f"\n💾 Saving configuration to {filename}")
    
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Configuration saved")


def main():
    """
    Main setup function to create all Cognito resources.
    """
    print("=" * 80)
    print("🚀 Cognito User Pool Setup for AgentCore Gateway")
    print("=" * 80)
    print()
    
    try:
        # Step 1: Create User Pool
        user_pool = create_user_pool()
        user_pool_id = user_pool['user_pool_id']
        print()
        
        # Step 2: Create Domain
        domain_prefix = create_user_pool_domain(user_pool_id)
        print()
        
        # Step 3: Create Resource Server with custom scope
        resource_server = create_resource_server(user_pool_id)
        print()
        
        # Step 4: Create App Client for M2M
        app_client = create_app_client(user_pool_id, resource_server['scope'])
        print()
        
        # Build configuration object
        config = {
            'user_pool_id': user_pool_id,
            'user_pool_arn': user_pool['arn'],
            'domain': f"{domain_prefix}.auth.us-west-2.amazoncognito.com",
            'domain_prefix': domain_prefix,
            'resource_server_identifier': resource_server['identifier'],
            'scope': resource_server['scope'],
            'client_id': app_client['client_id'],
            'client_secret': app_client['client_secret'],
            'token_endpoint': f"https://{domain_prefix}.auth.us-west-2.amazoncognito.com/oauth2/token",
            'discovery_url': f"https://cognito-idp.us-west-2.amazonaws.com/{user_pool_id}/.well-known/openid-configuration",
            'region': 'us-west-2'
        }
        
        # Save configuration
        save_config(config)
        
        # Print summary
        print()
        print("=" * 80)
        print("✅ Setup Complete!")
        print("=" * 80)
        print()
        print("📋 Configuration Summary:")
        print(f"   User Pool ID: {config['user_pool_id']}")
        print(f"   Domain: {config['domain']}")
        print(f"   Client ID: {config['client_id']}")
        print(f"   Scope: {config['scope']}")
        print(f"   Token Endpoint: {config['token_endpoint']}")
        print(f"   Discovery URL: {config['discovery_url']}")
        print()
        print("🔐 Client Secret saved to cognito_config.json")
        print()
        print("📝 Next Steps:")
        print("   1. Use the token endpoint to obtain access tokens")
        print("   2. Configure AgentCore Gateway with Custom JWT authorization")
        print("   3. Include the access token in gateway API requests")
        print()
        
    except Exception as e:
        print(f"\n❌ Error during setup: {str(e)}")
        raise


if __name__ == '__main__':
    main()
