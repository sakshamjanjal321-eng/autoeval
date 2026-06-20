from abc import ABC, abstractmethod
from autoeval.loader import LLMResponse, TestCase, EvaluatorConfig, EvaluationResult

class BaseEvaluator(ABC):
    @abstractmethod
    async def evaluate(self, response: LLMResponse, config: EvaluatorConfig, test_case: TestCase) -> EvaluationResult:
        """Evaluates the LLMResponse against the configuration and returns EvaluationResult."""
        pass
