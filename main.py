from app.core.orchestrator import Orchestrator
import asyncio



async def main():

    orchestrator = Orchestrator()
    await orchestrator.initialize()

  
    # Complaint Routing
 
    complaint_request = {
        "type": "complaint",
        "complaint_id": "COMP_0025"
    }

    result1 = await orchestrator.handle_request(complaint_request)
    print("\n=== DISPATCHER OUTPUT ===")
    print(result1)

    # Fraud Detection

    transaction_request = {
        "type": "transaction",
        "transaction_id": "TXN_0100"
    }

    result2 = await orchestrator.handle_request(transaction_request)
    print("\n=== SENTINEL OUTPUT ===")
    print(result2)

    
    # Product Recommendation

    recommendation_request = {
        "type": "recommendation",
        "customer_id": "CUST_0045"
    }

    result3 = await orchestrator.handle_request(recommendation_request)
    print("\n=== TRAJECTORY OUTPUT ===")
    print(result3)


if __name__ == "__main__":
    asyncio.run(main())