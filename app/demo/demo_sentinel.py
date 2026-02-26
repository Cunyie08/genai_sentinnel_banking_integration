# SENTINEL BANK - DEMO


import asyncio
from app.agents.sentinel_agent import SentinelAgent



# Helper function to run and display a scenario

async def run_scenario(agent, title: str, transaction_id: str):

    print("\n" + "=" * 60)
    print(f"SCENARIO: {title}")
    print("=" * 60)

    result = await agent.run({
        "transaction_id": transaction_id
    })

    print("\n--- SENTINEL DECISION ---")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Total Risk Score: {result['total_risk_score']}")
    print(f"ML Probability: {result.get('ml_probability', 'N/A')}")
    print(f"Requires Challenge: {result['requires_challenge']}")
    print(f"Recommended Action: {result['recommended_action']}")
    print(f"Confidence: {result['confidence']}")

    # Simulate push-to-app event
    if result["requires_challenge"]:
        print("\nPUSH NOTIFICATION SENT TO MOBILE APP")
        print("Awaiting biometric confirmation...")
        print("Biometric confirmed — transaction approved.")

    print("\n--- POLICY EXPLANATION ---")
    print(result["policy_explanation"])


# MAIN DEMO FLOW

async def main():

    print("\nInitializing Sentinel Agent\n")
    agent = SentinelAgent()
    transactions = agent.repo.dataset_loader.transactions

    # Scenario 1 - Clean Transaction (LOW risk)

    clean_txn = transactions[
        transactions["is_fraud_score"] == 0
    ].iloc[0]

    await run_scenario(
        agent,
        "Normal Mobile Transaction (Expected LOW Risk)",
        clean_txn["transaction_id"]
    )

   
    # Scenario 2 - Fraud Transaction (HIGH risk)

    fraud_txn = transactions[
        transactions["is_fraud_score"] == 1
    ].iloc[0]

    await run_scenario(
        agent,
        "Suspicious Transaction (Expected HIGH Risk)",
        fraud_txn["transaction_id"]
    )

    
    # Scenario 3 - ATM / POS Card Transaction: Mandatory Step-Up Authentication

    atm_txn = transactions[
        transactions["channel"] == "atm"
    ].iloc[0]

    await run_scenario(
        agent,
        "Card Transaction (Mandatory Push-to-App Challenge)",
        atm_txn["transaction_id"]
    )



# ENTRY POINT

if __name__ == "__main__":
    asyncio.run(main())