# Lambda function for Bedrock Knowledge Base policy retrieval
# Retrieves return policies from Bedrock Knowledge Base
# Reference: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-add-target-lambda.html

import json
import boto3
import os
from typing import Dict, Any, List

# Initialize AWS clients with us-west-2 region as per project standards
ssm = boto3.client('ssm', region_name='us-west-2')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-west-2')

# SSM parameter for Knowledge Base ID
KB_ID_PARAMETER = '/app/workshop/kb/knowledge-base-id'

# Cache the Knowledge Base ID to avoid repeated SSM calls
_kb_id_cache = None


def get_knowledge_base_id() -> str:
    """
    Retrieve Knowledge Base ID from SSM Parameter Store.
    
    Uses caching to avoid repeated SSM API calls within the same Lambda execution.
    
    Returns:
        str: Knowledge Base ID
    """
    global _kb_id_cache
    
    if _kb_id_cache is None:
        try:
            response = ssm.get_parameter(Name=KB_ID_PARAMETER)
            _kb_id_cache = response['Parameter']['Value']
            print(f"Retrieved Knowledge Base ID: {_kb_id_cache}")
        except Exception as e:
            print(f"Error retrieving Knowledge Base ID from SSM: {str(e)}")
            raise
    
    return _kb_id_cache


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for policy retrieval from Bedrock Knowledge Base.
    
    Handles the policy_retrieval tool which queries the Bedrock Knowledge Base
    for return policy information.
    
    Args:
        event: Input parameters containing the query
        context: Lambda context with bedrockAgentCoreToolName
        
    Returns:
        Dict: Policy information retrieved from Knowledge Base
    """
    try:
        # Extract tool name from context
        # Tool name format: ${target_name}___${tool_name}
        delimiter = "___"
        original_tool_name = context.client_context.custom['bedrockAgentCoreToolName']
        tool_name = original_tool_name[original_tool_name.index(delimiter) + len(delimiter):]
        
        # Verify this is the policy_retrieval tool
        if tool_name != 'policy_retrieval':
            return {
                'error': f'Unknown tool: {tool_name}',
                'expected_tool': 'policy_retrieval'
            }
        
        # Handle policy retrieval
        return handle_policy_retrieval(event)
        
    except Exception as e:
        # Log error with context for debugging
        print(f"Error processing request: {str(e)}")
        return {
            'error': f'Failed to process request: {str(e)}'
        }


def handle_policy_retrieval(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve return policy information from Bedrock Knowledge Base.
    
    Uses the Bedrock Agent Runtime retrieve API to search the Knowledge Base
    for relevant policy information based on the query.
    
    Args:
        event: Contains query string for policy search
        
    Returns:
        Dict: Policy information with relevant excerpts and metadata
    """
    query = event.get('query')
    
    if not query:
        return {'error': 'query parameter is required'}
    
    try:
        # Get Knowledge Base ID from SSM
        kb_id = get_knowledge_base_id()
        
        # Query the Bedrock Knowledge Base using retrieve API
        # Reference: https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent-runtime_Retrieve.html
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=kb_id,
            retrievalQuery={
                'text': query
            }
        )
        
        # Extract and format retrieval results
        retrieval_results = response.get('retrievalResults', [])
        
        if not retrieval_results:
            return {
                'found': False,
                'message': f'No policy information found for query: {query}',
                'query': query
            }
        
        # Format the results for easy consumption
        policies = []
        for result in retrieval_results:
            content = result.get('content', {})
            metadata = result.get('metadata', {})
            location = result.get('location', {})
            score = result.get('score', 0.0)
            
            # Extract text content
            text = content.get('text', '')
            
            # Extract relevant metadata
            country = metadata.get('country', 'Unknown')
            company = metadata.get('company', 'Unknown')
            page_number = metadata.get('x-amz-bedrock-kb-document-page-number', 'Unknown')
            
            # Extract source location
            source_uri = ''
            if location.get('type') == 'S3':
                s3_location = location.get('s3Location', {})
                source_uri = s3_location.get('uri', '')
            
            policies.append({
                'text': text,
                'relevance_score': score,
                'metadata': {
                    'country': country,
                    'company': company,
                    'page_number': page_number,
                    'source': source_uri
                }
            })
        
        return {
            'found': True,
            'query': query,
            'result_count': len(policies),
            'policies': policies,
            'knowledge_base_id': kb_id
        }
        
    except Exception as e:
        print(f"Error retrieving from Knowledge Base: {str(e)}")
        return {
            'error': f'Failed to retrieve policy information: {str(e)}',
            'query': query
        }
