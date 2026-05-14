# Policy Retrieval Lambda Function

This Lambda function retrieves return policy information from a Bedrock Knowledge Base for the Returns & Refunds Assistant.

## Overview

The function implements the `policy_retrieval` tool for AgentCore Gateway, which queries a Bedrock Knowledge Base containing return policy documents.

## Features

- Retrieves Knowledge Base ID from SSM Parameter Store
- Queries Bedrock Knowledge Base using the retrieve API
- Returns formatted policy excerpts with relevance scores
- Includes metadata (country, company, source document)
- Caches Knowledge Base ID for performance

## Tool Schema

### policy_retrieval

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "The policy query (e.g., 'return policy for electronics in the US')"
    }
  },
  "required": ["query"]
}
```

**Output Example:**
```json
{
  "found": true,
  "query": "return policy for electronics in the US",
  "result_count": 3,
  "policies": [
    {
      "text": "Most items can be returned within 30 days of delivery...",
      "relevance_score": 0.7385,
      "metadata": {
        "country": "US",
        "company": "Amazon",
        "page_number": 1.0,
        "source": "s3://bucket/Amazon-return-policy-us.pdf"
      }
    }
  ],
  "knowledge_base_id": "IQDULZAS7R"
}
```

## Configuration

### SSM Parameter

The Knowledge Base ID is stored in SSM Parameter Store:
- **Parameter Name**: `/app/workshop/kb/knowledge-base-id`
- **Value**: Knowledge Base ID (e.g., `IQDULZAS7R`)

### Knowledge Base

The Bedrock Knowledge Base should contain:
- Return policy documents (PDF format)
- Metadata tags: `country`, `company`
- Indexed for semantic search

## IAM Permissions Required

The Lambda execution role needs the following permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameter"
      ],
      "Resource": [
        "arn:aws:ssm:us-west-2:*:parameter/app/workshop/kb/knowledge-base-id"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:Retrieve"
      ],
      "Resource": [
        "arn:aws:bedrock:us-west-2:*:knowledge-base/*"
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
   zip -r policy_retrieval.zip handler.py
   ```

3. Deploy using AWS CLI or AWS Console

4. Configure as an AgentCore Gateway Lambda target

## Environment Variables

None required - Knowledge Base ID is retrieved from SSM Parameter Store.

## Region

All AWS operations target **us-west-2** region.

## Performance Considerations

- Knowledge Base ID is cached in memory to reduce SSM API calls
- Cache persists for the lifetime of the Lambda execution environment
- First invocation will be slightly slower due to SSM lookup

## Error Handling

The function handles the following error scenarios:
- Missing query parameter
- SSM parameter not found
- Knowledge Base not accessible
- No results found for query
- Bedrock API errors

All errors are returned in a structured format with descriptive messages.
