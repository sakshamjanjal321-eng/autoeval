import asyncio
from datetime import datetime
from typing import List, Optional

from autoeval.loader import TestSuite, TestSuiteResult, TestCaseResult, TestCase, LLMResponse, EvaluationResult
from autoeval.adapters.litellm import LiteLLMAdapter
from autoeval.evaluators.accuracy import AccuracyEvaluator
from autoeval.evaluators.cost import CostEvaluator
from autoeval.evaluators.hallucination import HallucinationEvaluator

class TestSuiteRunner:
    def __init__(self, suite: TestSuite, models: Optional[List[str]] = None, concurrency: int = 5, reporters: Optional[List[any]] = None):
        self.suite = suite
        self.models = models or suite.models or ["mock/good"]
        self.concurrency = concurrency
        self.reporters = reporters or []
        self.semaphore = asyncio.Semaphore(concurrency)
        
        # Instantiate evaluators
        self.evaluators = {
            "accuracy": AccuracyEvaluator(),
            "cost": CostEvaluator(),
            "hallucination": HallucinationEvaluator()
        }

    async def run(self) -> TestSuiteResult:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Initialize reporters
        for reporter in self.reporters:
            if hasattr(reporter, "on_start"):
                reporter.on_start(self.suite.name, self.models, self.suite.tests)
                
        # Generate tasks for all test case + model combinations
        tasks = []
        for test_case in self.suite.tests:
            for model in self.models:
                tasks.append(self._run_single_test_case_with_semaphore(model, test_case))
                
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        
        suite_result = TestSuiteResult(
            suite_name=self.suite.name,
            timestamp=timestamp,
            models_evaluated=self.models,
            results=results
        )
        
        # Notify completion
        for reporter in self.reporters:
            if hasattr(reporter, "on_complete"):
                reporter.on_complete(suite_result)
                
        return suite_result

    async def _run_single_test_case_with_semaphore(self, model: str, test_case: TestCase) -> TestCaseResult:
        async with self.semaphore:
            # Notify reporters test started
            for reporter in self.reporters:
                if hasattr(reporter, "on_test_start"):
                    reporter.on_test_start(model, test_case)
            
            # Setup adapter (using LiteLLMAdapter)
            adapter = LiteLLMAdapter(model_name=model)
            
            # Execute generation
            response = await adapter.generate(
                prompt=test_case.prompt,
                system_prompt=test_case.system_prompt
            )
            
            evaluations = []
            # Run all configured evaluators for this test case
            if not response.error:
                for eval_config in test_case.evaluators:
                    evaluator = self.evaluators.get(eval_config.type.lower())
                    if evaluator:
                        try:
                            eval_res = await evaluator.evaluate(response, eval_config, test_case)
                            evaluations.append(eval_res)
                        except Exception as e:
                            evaluations.append(EvaluationResult(
                                evaluator_type=eval_config.type,
                                score=0.0,
                                status="ERROR",
                                reason=f"Evaluator execution crashed: {str(e)}"
                            ))
                    else:
                        evaluations.append(EvaluationResult(
                            evaluator_type=eval_config.type,
                            score=0.0,
                            status="ERROR",
                            reason=f"Unknown evaluator type: '{eval_config.type}'"
                        ))
            
            test_case_result = TestCaseResult(
                test_case=test_case,
                model=model,
                response=response,
                evaluations=evaluations
            )
            
            # Notify reporters test completed
            for reporter in self.reporters:
                if hasattr(reporter, "on_test_complete"):
                    reporter.on_test_complete(test_case_result)
                    
            return test_case_result
