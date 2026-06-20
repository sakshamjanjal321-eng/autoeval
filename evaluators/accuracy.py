import re
from typing import Union, List, Any
from autoeval.evaluators.base import BaseEvaluator
from autoeval.loader import LLMResponse, TestCase, EvaluatorConfig, EvaluationResult

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

class AccuracyEvaluator(BaseEvaluator):
    async def evaluate(self, response: LLMResponse, config: EvaluatorConfig, test_case: TestCase) -> EvaluationResult:
        if response.error:
            return EvaluationResult(
                evaluator_type="accuracy",
                score=0.0,
                status="ERROR",
                reason=f"LLM generation failed: {response.error}"
            )
            
        method = (config.method or "exact").lower()
        output = response.output.strip()
        expected = config.expected
        
        if expected is None:
            return EvaluationResult(
                evaluator_type="accuracy",
                score=0.0,
                status="ERROR",
                reason="No expected output specified in evaluator configuration."
            )
            
        # Convert expected to a list for uniform handling
        expected_list = expected if isinstance(expected, list) else [expected]
        expected_list = [str(item) for item in expected_list]
        
        if method == "exact":
            for exp in expected_list:
                if output.lower() == exp.strip().lower():
                    return EvaluationResult(
                        evaluator_type="accuracy",
                        score=1.0,
                        status="PASS",
                        reason=f"Exact match found for: '{exp}'"
                    )
            return EvaluationResult(
                evaluator_type="accuracy",
                score=0.0,
                status="FAIL",
                reason=f"Expected one of {expected_list}, but got '{output}'"
            )
            
        elif method == "fuzzy":
            best_score = 0.0
            best_match = None
            
            for exp in expected_list:
                if fuzz:
                    # Use partial_ratio to check if expected answer exists inside the response
                    score = float(fuzz.partial_ratio(exp.strip().lower(), output.lower())) / 100.0
                else:
                    # Fallback simple substring similarity
                    score = 1.0 if exp.strip().lower() in output.lower() else 0.0
                    
                if score > best_score:
                    best_score = score
                    best_match = exp
                    
            threshold = config.threshold if config.threshold is not None else 0.8
            status = "PASS" if best_score >= threshold else "FAIL"
            
            return EvaluationResult(
                evaluator_type="accuracy",
                score=best_score,
                status=status,
                reason=f"Fuzzy score {best_score:.2f} for '{best_match}' (threshold: {threshold})"
            )
            
        elif method == "regex":
            for exp in expected_list:
                try:
                    if re.search(exp, output, re.IGNORECASE | re.DOTALL):
                        return EvaluationResult(
                            evaluator_type="accuracy",
                            score=1.0,
                            status="PASS",
                            reason=f"Regex pattern '{exp}' matched."
                        )
                except re.error as e:
                    return EvaluationResult(
                        evaluator_type="accuracy",
                        score=0.0,
                        status="ERROR",
                        reason=f"Invalid regex pattern '{exp}': {e}"
                    )
            return EvaluationResult(
                evaluator_type="accuracy",
                score=0.0,
                status="FAIL",
                reason=f"None of the regex patterns matched the output."
            )
            
        else:
            return EvaluationResult(
                evaluator_type="accuracy",
                score=0.0,
                status="ERROR",
                reason=f"Unknown accuracy evaluation method: {method}"
            )
