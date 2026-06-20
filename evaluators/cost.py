from autoeval.evaluators.base import BaseEvaluator
from autoeval.loader import LLMResponse, TestCase, EvaluatorConfig, EvaluationResult

class CostEvaluator(BaseEvaluator):
    async def evaluate(self, response: LLMResponse, config: EvaluatorConfig, test_case: TestCase) -> EvaluationResult:
        if response.error:
            return EvaluationResult(
                evaluator_type="cost",
                score=0.0,
                status="ERROR",
                reason=f"LLM generation failed: {response.error}"
            )
            
        failures = []
        
        # Check latency limit
        if config.max_latency is not None:
            if response.latency > config.max_latency:
                failures.append(f"Latency ({response.latency:.2f}s) exceeded limit of {config.max_latency}s")
                
        # Check token limit
        if config.max_tokens is not None:
            if response.total_tokens > config.max_tokens:
                failures.append(f"Total tokens ({response.total_tokens}) exceeded limit of {config.max_tokens}")
                
        # Check cost limit
        if config.max_cost is not None:
            if response.cost > config.max_cost:
                failures.append(f"Cost (${response.cost:.6f}) exceeded limit of ${config.max_cost:.6f}")
                
        if failures:
            return EvaluationResult(
                evaluator_type="cost",
                score=0.0,
                status="FAIL",
                reason=" | ".join(failures)
            )
            
        # All checks passed
        reasons = [f"Latency: {response.latency:.2f}s", f"Tokens: {response.total_tokens}", f"Cost: ${response.cost:.6f}"]
        return EvaluationResult(
            evaluator_type="cost",
            score=1.0,
            status="PASS",
            reason="All constraints met. " + " | ".join(reasons)
        )
