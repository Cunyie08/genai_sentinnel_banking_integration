from app.core.orchestrator import Orchestrator
import asyncio


# Complaint Routing
async def main():
        orchestrator = Orchestrator()
        await orchestrator.initialize()
        
        complaint_id = (
            orchestrator.repo.dataset_loader.complaints
            .iloc[250]["complaint_id"]
        )

        complaint_request = {
            "type": "complaint",
            "department": "complaint",
            "complaint_id": complaint_id,
            "agent": "DispatcherAgent" 
        }

        result1 = await orchestrator.handle_request(complaint_request)
        print("\n=== DISPATCHER OUTPUT ===")
        print(result1)

        # Fraud Detection

        transaction_id = (
            orchestrator.repo.dataset_loader.transactions
            .iloc[250]["transaction_id"]
        )

        transaction_request = {
            "type": "transaction",
            "department": "transaction",
            "transaction_id": transaction_id,
            "agent": "SentinelAgent"
        }

        result2 = await orchestrator.handle_request(transaction_request)
        print("\n=== SENTINEL OUTPUT ===")
        print(result2)

        
        # Product Recommendation

        recommendation_id = (
            orchestrator.repo.dataset_loader.transactions
            .iloc[250]["customer_id"]
        )

        recommendation_request = {
            "type": "recommendation",
            "department": "recommendation",
            "customer_id": recommendation_id,
            "agent": "TrajectoryAgent"
        }

        result3 = await orchestrator.handle_request(recommendation_request)
        print("\n=== TRAJECTORY OUTPUT ===")
        print(result3)


if __name__ == "__main__":
    asyncio.run(main())




