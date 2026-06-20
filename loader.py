import yaml
from typing import List, Optional, Any, Dict, Union
from pydantic import BaseModel, Field, model_validator

class EvaluatorConfig(BaseModel):
    type: str  # accuracy, hallucination, cost
    method: Optional[str] = None  # exact, fuzzy, regex, self_check, rag_grounding
    expected: Optional[Any] = None  # Expected string, pattern, or list for accuracy
    threshold: Optional[float] = 0.8  # Threshold for fuzzy match or LLM scoring
    max_latency: Optional[float] = None  # For latency checks
    max_cost: Optional[float] = None  # For pricing checks
    max_tokens: Optional[int] = None  # For token limit checks
    judge_model: Optional[str] = "gemini/gemini-1.5-flash"  # Default judge model for LLM evaluations
    check: Optional[str] = None  # Custom checks, e.g. "must_refuse"

class TestCase(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    prompt: str
    system_prompt: Optional[str] = None
    context: Optional[str] = None
    expected: Optional[Any] = None
    evaluator: Optional[Union[str, List[str]]] = None
    evaluators: List[EvaluatorConfig] = Field(default_factory=list)
    check: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Sync id and name
            tc_id = data.get("id")
            tc_name = data.get("name")
            if tc_id and not tc_name:
                data["name"] = tc_id
            elif tc_name and not tc_id:
                data["id"] = tc_name
                
            # If expected is present, synchronize with config
            expected = data.get("expected")
            check = data.get("check")
            
            # Map simple evaluator string(s) to EvaluatorConfig(s)
            evaluator_field = data.get("evaluator")
            if evaluator_field:
                eval_list = [evaluator_field] if isinstance(evaluator_field, str) else evaluator_field
                eval_configs = data.get("evaluators", [])
                
                for ev in eval_list:
                    ev_lower = ev.lower()
                    if ev_lower == "accuracy":
                        eval_configs.append({
                            "type": "accuracy",
                            "method": "exact" if expected else "fuzzy",
                            "expected": expected
                        })
                    elif ev_lower == "hallucination":
                        eval_configs.append({
                            "type": "hallucination",
                            "method": "self_check" if not data.get("context") else "rag_grounding",
                            "check": check
                        })
                    elif ev_lower == "cost":
                        eval_configs.append({
                            "type": "cost"
                        })
                data["evaluators"] = eval_configs
                
        return data

class TestSuite(BaseModel):
    name: str
    description: Optional[str] = None
    models: List[str] = Field(default_factory=list)
    evaluators: List[Union[str, EvaluatorConfig]] = Field(default_factory=list)
    tests: List[TestCase] = Field(default_factory=list)
    cases: List[TestCase] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_suite(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Sync tests and cases
            tests = data.get("tests")
            cases = data.get("cases")
            if tests and not cases:
                data["cases"] = tests
            elif cases and not tests:
                data["tests"] = cases
        return data

class LLMResponse(BaseModel):
    model: str
    output: str
    latency: float
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost: float = 0.0
    error: Optional[str] = None

class EvaluationResult(BaseModel):
    evaluator_type: str
    score: float  # 0.0 to 1.0
    status: str  # PASS, FAIL, ERROR
    reason: Optional[str] = None

class TestCaseResult(BaseModel):
    test_case: TestCase
    model: str
    response: LLMResponse
    evaluations: List[EvaluationResult] = Field(default_factory=list)

class TestSuiteResult(BaseModel):
    suite_name: str
    timestamp: str
    models_evaluated: List[str] = Field(default_factory=list)
    results: List[TestCaseResult] = Field(default_factory=list)

def load_suite(file_path: str) -> TestSuite:
    """Loads and validates a TestSuite from a YAML file."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    
    suite = TestSuite.model_validate(data)
    
    # Resolve global evaluators if they are string-based
    suite_eval_configs = []
    for ev in suite.evaluators:
        if isinstance(ev, str):
            ev_lower = ev.lower()
            if ev_lower == "accuracy":
                suite_eval_configs.append(EvaluatorConfig(type="accuracy", method="exact"))
            elif ev_lower == "hallucination":
                suite_eval_configs.append(EvaluatorConfig(type="hallucination", method="self_check"))
            elif ev_lower == "cost":
                suite_eval_configs.append(EvaluatorConfig(type="cost"))
        else:
            suite_eval_configs.append(ev)
            
    # Apply suite-level defaults if tests have no evaluators
    for test in suite.tests:
        if not test.evaluators:
            # We copy suite configs but inject test-specific details if needed
            test_evals = []
            for se in suite_eval_configs:
                config_copy = se.model_copy(deep=True)
                if config_copy.type == "accuracy" and test.expected:
                    config_copy.expected = test.expected
                    config_copy.method = "exact"
                elif config_copy.type == "hallucination":
                    config_copy.method = "self_check" if not test.context else "rag_grounding"
                    config_copy.check = test.check
                test_evals.append(config_copy)
            test.evaluators = test_evals
            
    return suite
