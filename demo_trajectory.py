
# SENTINNEL BANK — TRAJECTORY CONTROLLED DEMO PRS-001 v2.2  
# Priority Engine | DSR Validation | RAG Grounded


import asyncio
from app.agents.trajectory_agent import TrajectoryAgent


# Controlled Customer Profiles (Story-Based Demonstration)

CONTROLLED_CASES = [

    {
        "label": "High-income salaried professional — Car Loan candidate",
        "customer_data": {
            "Loan_signal_score": 0.84,
            "monthly_inflow": 650_000,
            "salary_detected": True,
            "uber_tracker": 15,
            "age": 32,
            "account_type": "current",
            "current_balance": 420_000,
            "desired_loan_amount": 3_000_000,
        }
    },

    {
        "label": "Student profile — Student Loan priority case",
        "customer_data": {
            "Loan_signal_score": 0.89,
            "monthly_inflow": 120_000,
            "salary_detected": False,
            "uber_tracker": 2,
            "age": 22,
            "account_type": "solo",
            "current_balance": 55_000,
            "desired_loan_amount": 500_000,
        }
    },

    {
        "label": "High net-worth client — Investment Plan case",
        "customer_data": {
            "Loan_signal_score": 0.78,
            "monthly_inflow": 3_500_000,
            "salary_detected": True,
            "uber_tracker": 5,
            "age": 45,
            "account_type": "current",
            "current_balance": 9_500_000,
        }
    },

    {
        "label": "DSR breach example — Loan exceeds CBN 33.3% cap",
        "customer_data": {
            "Loan_signal_score": 0.82,
            "monthly_inflow": 300_000,
            "salary_detected": True,
            "uber_tracker": 8,
            "age": 35,
            "account_type": "current",
            "current_balance": 200_000,
            "desired_loan_amount": 5_000_000,
        }
    },

    {
        "label": "Below eligibility thresholds — Rejection case",
        "customer_data": {
            "Loan_signal_score": 0.55,
            "monthly_inflow": 80_000,
            "salary_detected": False,
            "uber_tracker": 1,
            "age": 26,
            "account_type": "savings",
            "current_balance": 20_000,
        }
    },
]


# DEMO RUNNER


async def run_controlled_demo():

    print("\n" + "=" * 75)
    print("SENTINEL BANK — CONTROLLED PRODUCT RECOMMENDATION DEMO")
    print("PRS-001 v2.2 | Priority Logic | DSR | RAG Validation")
    print("=" * 75)

    agent = TrajectoryAgent()

    for index, case in enumerate(CONTROLLED_CASES, start=1):

        print("\n" + "━" * 70)
        print(f"CASE {index}: {case['label']}")
        print("━" * 70)

        # Call deterministic policy engine directly
        from app.rag.rag_system import recommend_product

        recommendation = recommend_product(case["customer_data"])

        primary_product = recommendation.get("primary_product")

        print(f"Recommended Product : {primary_product}")
        print(f"Confidence Level    : {recommendation['confidence']}")

        if recommendation["monthly_emi"] > 0:
            print(f"Monthly EMI         : ₦{recommendation['monthly_emi']:,.2f}")
            print(f"Tenure              : {recommendation['tenure_months']} months")
            print(f"DSR Ratio           : {recommendation['dsr_ratio']}")

            if recommendation["dsr_warning"]:
                print("⚠ WARNING: DSR exceeds CBN 33.3% regulatory cap")

        print("\nMet Criteria:")
        for item in recommendation["met_criteria"]:
            print(f"  + {item}")

        if recommendation["unmet_criteria"]:
            print("\nUnmet Criteria:")
            for item in recommendation["unmet_criteria"]:
                print(f"  - {item}")


        # RAG Validation Layer
        if primary_product:
            validation = await agent.rag_engine.validate_product_recommendation(
                case["customer_data"],
                primary_product
            )

            print("\nRAG Eligibility Validation:")
            print(f"  Recommendation : {validation['recommendation']}")
            print(f"  Confidence     : {validation['confidence']:.1%}")

        else:
            print("\nNo qualifying product — Below minimum thresholds.")

    print("\n" + "=" * 75)
    print("DEMO COMPLETE")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    asyncio.run(run_controlled_demo())