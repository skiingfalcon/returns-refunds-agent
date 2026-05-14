#!/usr/bin/env python3
"""
Test Lambda functions locally by simulating AgentCore Gateway context.

This script tests the Lambda functions with mock context objects that simulate
the bedrockAgentCoreToolName parameter.
"""

import json
import sys
import os

# Add lambda_functions to path
sys.path.insert(0, 'lambda_functions/data_lookup')
sys.path.insert(0, 'lambda_functions/policy_retrieval')

# Import handlers
from lambda_functions.data_lookup import handler as data_lookup_handler
from lambda_functions.policy_retrieval import handler as policy_handler


class MockContext:
    """Mock Lambda context object with AgentCore Gateway metadata."""
    
    def __init__(self, tool_name: str):
        self.client_context = MockClientContext(tool_name)
        self.function_name = 'test-function'
        self.function_version = '$LATEST'
        self.invoked_function_arn = 'arn:aws:lambda:us-west-2:123456789012:function:test'
        self.memory_limit_in_mb = 256
        self.aws_request_id = 'test-request-id'
        self.log_group_name = '/aws/lambda/test'
        self.log_stream_name = 'test-stream'


class MockClientContext:
    """Mock client context with AgentCore Gateway custom attributes."""
    
    def __init__(self, tool_name: str):
        # Simulate AgentCore Gateway tool name format: ${target_name}___${tool_name}
        self.custom = {
            'bedrockAgentCoreToolName': f'data_lookup_target___{tool_name}',
            'bedrockAgentCoreMessageVersion': '1.0',
            'bedrockAgentCoreAwsRequestId': 'test-aws-request-id',
            'bedrockAgentCoreMcpMessageId': 'test-mcp-message-id',
            'bedrockAgentCoreGatewayId': 'test-gateway-id',
            'bedrockAgentCoreTargetId': 'test-target-id'
        }


def test_order_lookup():
    """Test order lookup for customer C-01."""
    print("=" * 80)
    print("🧪 Test 1: Data Lookup Lambda - Order Lookup")
    print("=" * 80)
    print("Function: returns-refunds-data-lookup")
    print("Tool: order_lookup")
    print("Input: customer_id = C-01")
    print()
    
    event = {'customer_id': 'C-01'}
    context = MockContext('order_lookup')
    
    try:
        response = data_lookup_handler.lambda_handler(event, context)
        print("✅ Response:")
        print(json.dumps(response, indent=2))
        return response
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_user_lookup():
    """Test user lookup for customer C-01."""
    print("\n" + "=" * 80)
    print("🧪 Test 2: Data Lookup Lambda - User Lookup")
    print("=" * 80)
    print("Function: returns-refunds-data-lookup")
    print("Tool: user_lookup")
    print("Input: customer_id = C-01")
    print()
    
    event = {'customer_id': 'C-01'}
    context = MockContext('user_lookup')
    
    try:
        response = data_lookup_handler.lambda_handler(event, context)
        print("✅ Response:")
        print(json.dumps(response, indent=2))
        return response
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_product_lookup():
    """Test product lookup for product P-001."""
    print("\n" + "=" * 80)
    print("🧪 Test 3: Data Lookup Lambda - Product Lookup")
    print("=" * 80)
    print("Function: returns-refunds-data-lookup")
    print("Tool: product_lookup")
    print("Input: product_id = P-001")
    print()
    
    event = {'product_id': 'P-001'}
    context = MockContext('product_lookup')
    
    try:
        response = data_lookup_handler.lambda_handler(event, context)
        print("✅ Response:")
        print(json.dumps(response, indent=2))
        return response
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_policy_retrieval():
    """Test policy retrieval for electronics in the US."""
    print("\n" + "=" * 80)
    print("🧪 Test 4: Policy Retrieval Lambda")
    print("=" * 80)
    print("Function: returns-refunds-policy-retrieval")
    print("Tool: policy_retrieval")
    print("Input: query = What is the return policy for electronics in the US?")
    print()
    
    event = {'query': 'What is the return policy for electronics in the US?'}
    
    # Create context with policy_retrieval tool name
    context = MockContext('policy_retrieval')
    context.client_context.custom['bedrockAgentCoreToolName'] = 'policy_target___policy_retrieval'
    
    try:
        response = policy_handler.lambda_handler(event, context)
        print("✅ Response:")
        print(json.dumps(response, indent=2, default=str))
        return response
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Run all tests."""
    print("\n🚀 Lambda Function Test Suite")
    print("Testing deployed Lambda functions with simulated AgentCore Gateway context\n")
    
    results = {
        'order_lookup': test_order_lookup(),
        'user_lookup': test_user_lookup(),
        'product_lookup': test_product_lookup(),
        'policy_retrieval': test_policy_retrieval()
    }
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    
    passed = sum(1 for r in results.values() if r is not None and 'error' not in r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result is not None and 'error' not in result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 80)


if __name__ == '__main__':
    main()
