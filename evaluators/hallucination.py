import json
import re
import asyncio
from typing import Optional
import litellm
from litellm import acompletion

from autoeval.evaluators.base import BaseEvaluator
from autoeval.loader import LLMResponse, TestCase, EvaluatorConfig, EvaluationResult

SYSTEM_PROMPT_SELF_CHECK = (
    "You are an expert AI evaluator. Your task is to analyze an AI model's response and judge if it is "
    "coherent, self-consistent, and free of hallucinations or logical contradictions.\n"
    "Provide your response in JSON format containing:\n"
    "1. 'score': A float between 0.0 (completely hallucinated, contradictory, or incoherent) and 1.0 (perfectly factual, logical, and coherent).\n"
    "2. 'reason': A brief explanation of your reasoning.\n"
    "Respond ONLY with the JSON object."
)

PROMPT_SELF_CHECK_TEMPLATE = (
    "Original Prompt: {prompt}\n\n"
    "Generated Response:\n{output}\n"
)

SYSTEM_PROMPT_RAG_GROUNDING = (
    "You are an expert AI evaluator. Your task is to analyze if an AI model's response is grounded in and "
    "fully supported by the provided context. Any claim in the response that cannot be verified from the "
    "context should lower the score.\n"
    "Provide your response in JSON format containing:\n"
    "1. 'score': A float between 0.0 (not grounded at all, relies entirely on outside info or hallucinations) and 1.0 (fully grounded, every statement is supported by the context).\n"
    "2. 'reason': A brief explanation pointing out any ungrounded assertions.\n"
    "Respond ONLY with the JSON object."
)

PROMPT_RAG_GROUNDING_TEMPLATE = (
    "Context:\n{context}\n\n"
    "Original Prompt: {prompt}\n\n"
    "Generated Response:\n{output}\n"
)

class HallucinationEvaluator(BaseEvaluator):
    async def evaluate(self, response: LLMResponse, config: EvaluatorConfig, test_case: TestCase) -> EvaluationResult:
        if response.error:
            return EvaluationResult(
                evaluator_type="hallucination",
                score=0.0,
                status="ERROR",
                reason=f"LLM generation failed: {response.error}"
            )
            
        method = (config.method or "self_check").lower()
        judge_model = config.judge_model or "gemini/gemini-1.5-flash"
        
        # Check for must_refuse check
        if config.check == "must_refuse":
            output_lower = response.output.lower()
            refusal_keywords = [
                "cannot fulfill", "don't have", "do not have", "does not exist", "doesn't exist",
                "fake", "artificial", "not a real", "sorry", "cannot find", "unable to",
                "no record", "cannot summarize", "i am an ai", "as an ai", "not aware"
            ]
            if any(keyword in output_lower for keyword in refusal_keywords):
                return EvaluationResult(
                    evaluator_type="hallucination",
                    score=1.0,
                    status="PASS",
                    reason="Correctly refused to answer/hallucinate (matched refusal pattern)."
                )
            else:
                if judge_model.startswith("mock/") or response.model.startswith("mock/"):
                    return EvaluationResult(
                        evaluator_type="hallucination",
                        score=0.0,
                        status="FAIL",
                        reason="Failed to refuse to answer/hallucinate about a fake topic."
                    )
        
        # Build prompt and system prompt
        if method == "self_check":
            system_prompt = SYSTEM_PROMPT_SELF_CHECK
            user_prompt = PROMPT_SELF_CHECK_TEMPLATE.format(
                prompt=test_case.prompt,
                output=response.output
            )
        elif method == "rag_grounding":
            if not test_case.context:
                return EvaluationResult(
                    evaluator_type="hallucination",
                    score=0.0,
                    status="ERROR",
                    reason="RAG Grounding evaluation requires a context field in the test case."
                )
            system_prompt = SYSTEM_PROMPT_RAG_GROUNDING
            user_prompt = PROMPT_RAG_GROUNDING_TEMPLATE.format(
                context=test_case.context,
                prompt=test_case.prompt,
                output=response.output
            )
        else:
            return EvaluationResult(
                evaluator_type="hallucination",
                score=0.0,
                status="ERROR",
                reason=f"Unknown hallucination evaluation method: {method}"
            )
            
        # Fallback/mock check
        if judge_model.startswith("mock/") or response.model.startswith("mock/"):
            await asyncio.sleep(0.1)
            # Heuristic simulation for testing
            output_lower = response.output.lower()
            if "hallucinated" in output_lower or "ungrounded" in output_lower:
                score = 0.2
                reason = "Mock Judge: Detected ungrounded/hallucinated statements."
            else:
                score = 1.0
                reason = "Mock Judge: Response is coherent and well grounded."
                
            threshold = config.threshold if config.threshold is not None else 0.8
            status = "PASS" if score >= threshold else "FAIL"
            return EvaluationResult(
                evaluator_type="hallucination",
                score=score,
                status=status,
                reason=reason
            )
            
        # Call the judge model
        try:
            res = await acompletion(
                model=judge_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"} if "gpt" in judge_model.lower() or "gemini" in judge_model.lower() else None
            )
            
            judge_output = res.choices[0].message.content or ""
            
            # Extract JSON block
            json_match = re.search(r"\{.*\}", judge_output, re.DOTALL)
            if json_match:
                result_data = json.loads(json_match.group(0))
            else:
                result_data = json.loads(judge_output)
                
            score = float(result_data.get("score", 0.0))
            reason = result_data.get("reason", "No reason provided by LLM judge.")
            
            threshold = config.threshold if config.threshold is not None else 0.8
            status = "PASS" if score >= threshold else "FAIL"
            
            return EvaluationResult(
                evaluator_type="hallucination",
                score=score,
                status=status,
                reason=f"Judge ({judge_model}): {reason}"
            )
            
        except Exception as e:
            # Fallback to self-evaluation if API call fails
            return EvaluationResult(
                evaluator_type="hallucination",
                score=0.0,
                status="ERROR",
                reason=f"Failed to query LLM judge: {str(e)}"
            )
