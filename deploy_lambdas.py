#!/usr/bin/env python3
"""
Deploy Lambda functions for Returns & Refunds Assistant.

This script:
1. Zips each Lambda function's code
2. Retrieves the Lambda execution role ARN from SSM
3. Creates Lambda functions in AWS us-west-2 region
4. Prints the deployed Lambda ARNs
"""

import boto3
import zipfile
import os
from typing import Dict

# Initialize AWS clients with us-west-2 region as per project standards
ssm = boto3.client('ssm', region_name='us-west-2')
lambda_client = boto3.client('lambda', region_name='us-west-2')

# SSM parameter for Lambda execution role
EXECUTION_ROLE_PARAMETER = '/app/workshop/lambda/execution-role-arn'

# Lambda function configurations
LAMBDA_FUNCTIONS = {
    'data_lookup': {
        'name': 'returns-refunds-data-lookup',
        'handler': 'handler.lambda_handler',
        'runtime': 'python3.13',
        'timeout': 30,
        'memory': 256,
        'description': 'Handles order, customer, and product lookups from DynamoDB',
        'source_dir': 'lambda_functions/data_lookup',
        'zip_file': 'lambda_functions/data_lookup.zip'
    },
    'policy_retrieval': {
        'name': 'returns-refunds-policy-retrieval',
        'handler': 'handler.lambda_handler',
        'runtime': 'python3.13',
        'timeout': 60,
        'memory': 512,
        'description': 'Retrieves return policies from Bedrock Knowledge Base',
        'source_dir': 'lambda_functions/policy_retrieval',
        'zip_file': 'lambda_functions/policy_retrieval.zip'
    }
}


def get_execution_role_arn() -> str:
    """
    Retrieve Lambda execution role ARN from SSM Parameter Store.
    
    Returns:
        str: Lambda execution role ARN
    """
    print(f"📥 Retrieving execution role ARN from SSM parameter: {EXECUTION_ROLE_PARAMETER}")
    
    try:
        response = ssm.get_parameter(Name=EXECUTION_ROLE_PARAMETER)
        role_arn = response['Parameter']['Value']
        print(f"✅ Retrieved role ARN: {role_arn}")
        return role_arn
    except Exception as e:
        print(f"❌ Error retrieving execution role ARN: {str(e)}")
        raise


def create_zip_file(source_dir: str, zip_path: str) -> None:
    """
    Create a zip file containing the Lambda function code.
    
    Args:
        source_dir: Directory containing the Lambda function code
        zip_path: Path where the zip file should be created
    """
    print(f"📦 Creating zip file: {zip_path}")
    
    # Remove existing zip file if it exists
    if os.path.exists(zip_path):
        os.remove(zip_path)
    
    # Create zip file with handler.py
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        handler_path = os.path.join(source_dir, 'handler.py')
        if os.path.exists(handler_path):
            zipf.write(handler_path, 'handler.py')
            print(f"  ✅ Added handler.py to zip")
        else:
            raise FileNotFoundError(f"Handler file not found: {handler_path}")
    
    # Verify zip file was created
    zip_size = os.path.getsize(zip_path)
    print(f"  ✅ Zip file created: {zip_size} bytes")


def create_or_update_lambda(config: Dict, role_arn: str) -> str:
    """
    Create or update a Lambda function.
    
    Args:
        config: Lambda function configuration
        role_arn: IAM role ARN for Lambda execution
        
    Returns:
        str: Lambda function ARN
    """
    function_name = config['name']
    zip_path = config['zip_file']
    
    print(f"\n🚀 Deploying Lambda function: {function_name}")
    
    # Read zip file contents
    with open(zip_path, 'rb') as f:
        zip_contents = f.read()
    
    try:
        # Try to get existing function
        lambda_client.get_function(FunctionName=function_name)
        
        # Function exists, update it
        print(f"  📝 Function exists, updating code...")
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_contents
        )
        
        # Update configuration
        print(f"  ⚙️  Updating configuration...")
        config_response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Runtime=config['runtime'],
            Role=role_arn,
            Handler=config['handler'],
            Description=config['description'],
            Timeout=config['timeout'],
            MemorySize=config['memory']
        )
        
        function_arn = response['FunctionArn']
        print(f"  ✅ Updated Lambda function")
        
    except lambda_client.exceptions.ResourceNotFoundException:
        # Function doesn't exist, create it
        print(f"  🆕 Creating new Lambda function...")
        response = lambda_client.create_function(
            FunctionName=function_name,
            Runtime=config['runtime'],
            Role=role_arn,
            Handler=config['handler'],
            Code={'ZipFile': zip_contents},
            Description=config['description'],
            Timeout=config['timeout'],
            MemorySize=config['memory'],
            Publish=True
        )
        
        function_arn = response['FunctionArn']
        print(f"  ✅ Created Lambda function")
    
    return function_arn


def main():
    """Main deployment function."""
    print("=" * 80)
    print("🚀 Lambda Function Deployment Script")
    print("=" * 80)
    print(f"Region: us-west-2")
    print(f"Functions to deploy: {len(LAMBDA_FUNCTIONS)}")
    print()
    
    try:
        # Step 1: Get execution role ARN
        role_arn = get_execution_role_arn()
        print()
        
        # Step 2: Create zip files and deploy Lambda functions
        deployed_functions = {}
        
        for func_key, config in LAMBDA_FUNCTIONS.items():
            # Create zip file
            create_zip_file(config['source_dir'], config['zip_file'])
            
            # Deploy Lambda function
            function_arn = create_or_update_lambda(config, role_arn)
            deployed_functions[func_key] = {
                'name': config['name'],
                'arn': function_arn
            }
        
        # Step 3: Print summary
        print("\n" + "=" * 80)
        print("✅ Deployment Complete!")
        print("=" * 80)
        print("\n📋 Deployed Lambda Functions:\n")
        
        for func_key, info in deployed_functions.items():
            print(f"  {func_key}:")
            print(f"    Name: {info['name']}")
            print(f"    ARN:  {info['arn']}")
            print()
        
        print("=" * 80)
        print("\n💡 Next Steps:")
        print("  1. Configure these Lambda functions as AgentCore Gateway targets")
        print("  2. Define tool schemas for each Lambda function")
        print("  3. Test the Lambda functions with sample events")
        print()
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {str(e)}")
        raise


if __name__ == '__main__':
    main()
