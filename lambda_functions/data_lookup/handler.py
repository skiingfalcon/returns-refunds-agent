# Lambda function for DynamoDB data lookups
# Handles order_lookup, user_lookup, and product_lookup tools
# Reference: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-add-target-lambda.html

import json
import boto3
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Initialize AWS clients with us-west-2 region as per project standards
dynamodb = boto3.client('dynamodb', region_name='us-west-2')

# DynamoDB table names
CUSTOMERS_TABLE = 'workshop-customers'
ORDERS_TABLE = 'workshop-orders'
PRODUCTS_TABLE = 'workshop-products'


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for data lookup tools.
    
    Handles three tools:
    - order_lookup: Look up orders by customer_id and product_id
    - user_lookup: Look up customer information by customer_id
    - product_lookup: Look up product information by product_id
    
    Args:
        event: Input parameters from the tool invocation
        context: Lambda context with bedrockAgentCoreToolName
        
    Returns:
        Dict: Tool response with the requested data
    """
    try:
        # Extract tool name from context
        # Tool name format: ${target_name}___${tool_name}
        delimiter = "___"
        original_tool_name = context.client_context.custom['bedrockAgentCoreToolName']
        tool_name = original_tool_name[original_tool_name.index(delimiter) + len(delimiter):]
        
        # Route to appropriate handler based on tool name
        if tool_name == 'order_lookup':
            return handle_order_lookup(event)
        elif tool_name == 'user_lookup':
            return handle_user_lookup(event)
        elif tool_name == 'product_lookup':
            return handle_product_lookup(event)
        else:
            return {
                'error': f'Unknown tool: {tool_name}',
                'available_tools': ['order_lookup', 'user_lookup', 'product_lookup']
            }
            
    except Exception as e:
        # Log error with context for debugging
        print(f"Error processing request: {str(e)}")
        return {
            'error': f'Failed to process request: {str(e)}'
        }


def handle_order_lookup(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Look up orders from DynamoDB workshop-orders table.
    
    The workshop-orders table has composite key:
    - HASH: customer_id (String)
    - RANGE: product_id (String)
    
    Args:
        event: Contains customer_id and optionally product_id
        
    Returns:
        Dict: Order details or list of orders for the customer
    """
    customer_id = event.get('customer_id')
    product_id = event.get('product_id')
    
    if not customer_id:
        return {'error': 'customer_id is required'}
    
    try:
        if product_id:
            # Query specific order with both keys
            response = dynamodb.get_item(
                TableName=ORDERS_TABLE,
                Key={
                    'customer_id': {'S': customer_id},
                    'product_id': {'S': product_id}
                }
            )
            
            if 'Item' not in response:
                return {
                    'found': False,
                    'message': f'No order found for customer {customer_id} and product {product_id}'
                }
            
            # Convert DynamoDB item to readable format
            item = response['Item']
            return {
                'found': True,
                'order': {
                    'customer_id': item.get('customer_id', {}).get('S'),
                    'product_id': item.get('product_id', {}).get('S'),
                    'purchased_date': item.get('purchased_date', {}).get('S'),
                    'status': item.get('status', {}).get('S')
                }
            }
        else:
            # Query all orders for customer
            response = dynamodb.query(
                TableName=ORDERS_TABLE,
                KeyConditionExpression='customer_id = :cid',
                ExpressionAttributeValues={
                    ':cid': {'S': customer_id}
                }
            )
            
            orders = []
            for item in response.get('Items', []):
                orders.append({
                    'customer_id': item.get('customer_id', {}).get('S'),
                    'product_id': item.get('product_id', {}).get('S'),
                    'purchased_date': item.get('purchased_date', {}).get('S'),
                    'status': item.get('status', {}).get('S')
                })
            
            return {
                'found': len(orders) > 0,
                'count': len(orders),
                'orders': orders
            }
            
    except Exception as e:
        print(f"Error querying orders: {str(e)}")
        return {'error': f'Failed to query orders: {str(e)}'}


def handle_user_lookup(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Look up customer information from DynamoDB workshop-customers table.
    
    The workshop-customers table has:
    - HASH: customer_id (String)
    
    Args:
        event: Contains customer_id
        
    Returns:
        Dict: Customer details including name and country_code
    """
    customer_id = event.get('customer_id')
    
    if not customer_id:
        return {'error': 'customer_id is required'}
    
    try:
        response = dynamodb.get_item(
            TableName=CUSTOMERS_TABLE,
            Key={
                'customer_id': {'S': customer_id}
            }
        )
        
        if 'Item' not in response:
            return {
                'found': False,
                'message': f'Customer {customer_id} not found'
            }
        
        # Convert DynamoDB item to readable format
        item = response['Item']
        return {
            'found': True,
            'customer': {
                'customer_id': item.get('customer_id', {}).get('S'),
                'name': item.get('name', {}).get('S'),
                'country_code': item.get('country_code', {}).get('S')
            }
        }
        
    except Exception as e:
        print(f"Error querying customer: {str(e)}")
        return {'error': f'Failed to query customer: {str(e)}'}


def handle_product_lookup(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Look up product information from DynamoDB workshop-products table.
    
    The workshop-products table has:
    - HASH: product_id (String)
    
    Args:
        event: Contains product_id
        
    Returns:
        Dict: Product details including name, provider, and category
    """
    product_id = event.get('product_id')
    
    if not product_id:
        return {'error': 'product_id is required'}
    
    try:
        response = dynamodb.get_item(
            TableName=PRODUCTS_TABLE,
            Key={
                'product_id': {'S': product_id}
            }
        )
        
        if 'Item' not in response:
            return {
                'found': False,
                'message': f'Product {product_id} not found'
            }
        
        # Convert DynamoDB item to readable format
        item = response['Item']
        return {
            'found': True,
            'product': {
                'product_id': item.get('product_id', {}).get('S'),
                'product_name': item.get('product_name', {}).get('S'),
                'provider': item.get('provider', {}).get('S'),
                'product_category': item.get('product_category', {}).get('S')
            }
        }
        
    except Exception as e:
        print(f"Error querying product: {str(e)}")
        return {'error': f'Failed to query product: {str(e)}'}
