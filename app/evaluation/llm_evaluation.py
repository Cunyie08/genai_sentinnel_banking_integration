# This file contains LLM acting as a Judge to evaluate the result (Who decided if the AI did well)

import re
from typing import Dict, Any, List


class LLMJudge: # 
    """
    Compares an agent's output with the ground-truth

    Takes two arguments, the agent's decision and the expected outcome

    Returns a structured evaluation result (e.g. pass/fail, confidence score, hallucination risk. etc.)
    """

    # General Checks (applies to all agents)

    @staticmethod
    def check_empty_output(result: Dict[str, Any]) -> float:
        """
        Returns 1.0 if reasoning field exists and is non-empty.
        """
        reasoning = result.get("reasoning", "")
        return 1.0 if reasoning and len(reasoning.strip()) > 20 else 0.0

    @staticmethod
    def check_schema_integrity(result: Dict[str, Any], required_fields: List[str]) -> float:
        """
        Ensures required fields are present.
        """
        missing = [f for f in required_fields if f not in result]
        return 1.0 if not missing else 0.0


    # Trajectory Checks

    @staticmethod
    def check_trajectory_policy_alignment(result: Dict[str, Any]) -> float:
        """
        Ensure LLM explanation does not contradict eligibility decision.
        """
        reasoning = result.get("reasoning", "").lower()
        is_eligible = result.get("is_eligible")

        if is_eligible and "not eligible" in reasoning:
            return 0.0

        if not is_eligible and "approved" in reasoning:
            return 0.0

        return 1.0

    @staticmethod
    def check_no_hallucinated_thresholds(result: Dict[str, Any]) -> float:
        """
        Prevent LLM from inventing new numeric thresholds.
        """
        reasoning = result.get("reasoning", "")

        # extract all numbers in explanation
        numbers = re.findall(r"\d+\.\d+|\d+", reasoning)

        # allowed numeric fields
        allowed_values = []

        if "score_range" in result and result["score_range"]:
            allowed_values.extend(
                [str(v) for v in result["score_range"]]
            )

        # simple validation: no unknown numeric thresholds
        for n in numbers:
            if n not in allowed_values and float(n) > 100:
                return 0.0

        return 1.0


    # Sentinel Checks
    @staticmethod
    def check_sentinel_consistency(result: Dict[str, Any]) -> float:
        """
        Ensure risk level matches numeric score.
        """
        score = result.get("total_risk_score", 0)
        level = result.get("risk_level", "")

        if score >= 86 and level != "CRITICAL":
            return 0.0

        if 61 <= score <= 85 and level != "HIGH":
            return 0.0

        return 1.0
    

    # Dispatcher Checks
    @staticmethod
    def check_dispatcher_department_present(result: Dict[str, Any]) -> float:
        """
        Ensure department_code exists.
        """
        return 1.0 if result.get("department_code") else 0.0


    # Master Evaluation Entry

    @classmethod
    def evaluate(cls, agent_name: str, result: Dict[str, Any]) -> Dict[str, float]:
        """
        Unified evaluation entry.
        """

        metrics = {
            "non_empty_reasoning": cls.check_empty_output(result)
        }

        if agent_name == "TrajectoryAgent":
            metrics.update({
                "policy_alignment": cls.check_trajectory_policy_alignment(result),
                "no_hallucinated_thresholds": cls.check_no_hallucinated_thresholds(result),
            })

        elif agent_name == "SentinelAgent":
            metrics.update({
                "risk_consistency": cls.check_sentinel_consistency(result),
            })

        elif agent_name == "DispatcherAgent":
            metrics.update({
                "department_present": cls.check_dispatcher_department_present(result),
            })

        return metrics