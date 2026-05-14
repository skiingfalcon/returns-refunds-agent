# Data Lookup Lambda Function

This Lambda function handles DynamoDB lookups for orders, customers, and products for the Returns & Refunds Assistant.

## Overview

The function implements three tools for AgentCore Gateway:
- `order_lookup`: Query orders from the workshop-orders table
- `user_lookup`: Query customer information from the workshop-customers table  
- `product_lookup`: Query product information from the workshop-products table

## DynamoDB Table Structures

### workshop-customers
- **Primary Key**: `customer_id` (String, HASH)
- **Attributes**: `name`, `country_code`

### workshop-orders
- **Primary Key**: 
  - `customer_id` (String, HASH)
  - `product_id` (String, RANGE)
- **Attributes**: `purchased_date`, `status`

### workshop-products
- **Primary Key**: `product_id` (String, HASH)
- **Attributes**: `product_name`, `provider`, `product_category`

## Tool Schemas

### order_lookup

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "customer_id": {
      "type": "string",
      "description": "The customer ID to look up orders for"
    },
    "product_id": {
      "type": "string",
      "description": "Optional product ID to look up a specific order"
    }
  },
  "required": ["customer_id"]
}
```

**Output Example:**
```json
{
  "found": true,
  "count": 2,
  "orders": [
    {
      "customer_id": "C-01",
      "product_id": "P-001",
      "purchased_date": "2024-01-15",
      "status": "DELIVERED"
    }
  ]
}
```

### user_lookup

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "customer_id": {
      "type": "string",
      "description": "The customer ID to look up"
    }
  },
  "required": ["customer_id"]
}
```

**Output Example:**
```json
{
  "found": true,
  "customer": {
    "customer_id": "C-01",
    "name": "Rajesh Kumar",
    "country_code": "IN"
  }
}
```

### product_lookup

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "product_id": {
      "type": "string",
      "description": "The product ID to look up"
    }
  },
  "required": ["product_id"]
}
```

**Output Example:**
```json
{
  "found": true,
  "product": {
    "product_id": "P-001",
    "product_name": "iPhone 15 Pro",
    "provider": "Apple",
    "product_category": "phone"
  }
}
```

## IAM Permissions Required

The Lambda execution role needs the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-west-2:*:table/workshop-customers",
        "arn:aws:dynamodb:us-west-2:*:table/workshop-orders",
        "arn:aws:dynamodb:us-west-2:*:table/workshop-products"
      ]
    }
  ]
}
```

## Deployment

1. Install dependencies (if testing locally):
   ```bash
   pip install -r requirements.txt
   ```

2. Package the Lambda function:
   ```bash
   zip -r data_lookup.zip handler.py
   ```

3. Deploy using AWS CLI or AWS Console

4. Configure as an AgentCore Gateway Lambda target

## Environment Variables

None required - all configuration is hardcoded for the workshop environment.

## Region

All AWS operations target **us-west-2** region.
