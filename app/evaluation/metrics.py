# This file conatins the Precision , latency and efficiency (what measurements we care about?)


"""
Defining the evaluation metrics for Sentinnel Banking

This file contains what is measured. 
Metrics are defined as functions that take in the agent's output and return a dictionary of metric names and values."""

from typing import Dict, Any


class Metrics:
    """
    Central registry of evaluation metrics

    """
    @staticmethod
    def evaluate_triage(result: Dict[str, Any]) -> Dict[str, float]:
        """ 
    This is the percentage of complaints routed to the correct department.
    Goal: >95%
    """
        return {
            "confidence_score": result.get("confidence", 0.0),
            "has_department": 1.0 if result.get("department_code") else 0.0,
        }

    @staticmethod
    def evaluate_fraud(result: Dict[str, Any]) -> Dict[str, float]:

        return {
            "risk_score": result.get("total_risk_score", 0),
            "confidence": result.get("confidence", 0.0),
        }

    @staticmethod
    def evaluate_product_recommendation(result: Dict[str, Any]) -> Dict[str, float]:
        val = result.get("policy_validation") or {}
        return {
            "eligible": 1.0 if result.get("is_eligible") else 0.0,
            "policy_confidence": val.get("confidence", 0.0),
        }

    
