# Returns & Refunds Domain Knowledge

## Project Overview

This project implements a Returns & Refunds assistant using Strands Agents SDK and AgentCore CLI. The assistant helps customers and support staff process returns and refunds efficiently.

## Core Functionality

### Return Processing

The assistant should handle:
- Validating return eligibility (time windows, condition requirements)
- Generating return authorization numbers
- Providing return shipping labels
- Tracking return shipments
- Updating order status

### Refund Processing

The assistant should handle:
- Calculating refund amounts based on policy
- Processing full and partial refunds
- Handling different payment methods
- Generating refund confirmations
- Updating financial records

### Customer Support

The assistant should provide:
- Return policy information
- Status updates on returns/refunds
- Troubleshooting common issues
- Escalation to human agents when needed

## Business Rules

### Return Eligibility

- Standard return window: 30 days from delivery
- Items must be in original condition
- Some categories may have different policies (e.g., electronics: 14 days)
- Final sale items are not returnable

### Refund Policies

- Refunds processed to original payment method
- Shipping costs are non-refundable (unless item defective)
- Restocking fees may apply (typically 15% for opened items)
- Refunds processed within 5-7 business days after return received

### Special Cases

- Defective items: Full refund including shipping
- Wrong item shipped: Full refund including return shipping
- Damaged in transit: Full refund, no return required (with photo proof)

## Data Models

### Order
- order_id: Unique identifier
- customer_id: Customer identifier
- order_date: Purchase timestamp
- items: List of order items
- total_amount: Order total
- payment_method: Payment type
- status: Order status

### Return Request
- return_id: Unique identifier
- order_id: Associated order
- items: Items being returned
- reason: Return reason
- status: Return status
- created_date: Request timestamp

### Refund
- refund_id: Unique identifier
- order_id: Associated order
- return_id: Associated return (if applicable)
- amount: Refund amount
- status: Refund status
- processed_date: Processing timestamp

## Integration Points

### AWS Services

- **DynamoDB**: Store orders, returns, and refunds
- **Lambda**: Execute agent and tool functions
- **S3**: Store return labels and documentation
- **SES**: Send email notifications
- **EventBridge**: Trigger workflows and notifications

### External Services

- Payment processor API for refunds
- Shipping carrier API for labels
- Inventory management system
- Customer notification system

## Agent Capabilities

The Returns & Refunds agent should be able to:

1. **Answer Questions**: Provide information about return policies and procedures
2. **Check Status**: Look up status of returns and refunds
3. **Initiate Returns**: Start the return process for eligible orders
4. **Process Refunds**: Calculate and process refund amounts
5. **Generate Labels**: Create return shipping labels
6. **Escalate Issues**: Identify when human intervention is needed

## Conversation Patterns

### Happy Path
```
Customer: "I need to return my order #12345"
Agent: Checks order eligibility → Confirms return → Generates label → Provides instructions

Customer: "When will I get my refund?"
Agent: Checks return status → Provides timeline → Sends confirmation
```

### Exception Handling
```
Customer: "I want to return this item I bought 60 days ago"
Agent: Checks policy → Explains 30-day window → Offers alternatives or escalation

Customer: "The item arrived damaged"
Agent: Identifies special case → Processes immediate refund → No return required
```

## Success Metrics

- Return processing time < 2 minutes
- Refund processing time < 5 business days
- Customer satisfaction score > 4.5/5
- Escalation rate < 10%
- Successful resolution rate > 90%
