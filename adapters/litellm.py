import time
import asyncio
from typing import Optional
import litellm
from litellm import acompletion, completion_cost

from autoeval.adapters.base import BaseAdapter
from autoeval.loader import LLMResponse

class LiteLLMAdapter(BaseAdapter):
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> LLMResponse:
        start_time = time.perf_counter()
        
        # If it's a mock model, simulate completion to make testing/CI easy without API keys.
        if self.model_name.startswith("mock/"):
            await asyncio.sleep(0.1)  # Simulate network latency
            
            mock_type = self.model_name.split("/", 1)[1]
            
            # Simple heuristic mock responses for common tests
            prompt_lower = prompt.lower()
            if "capital of france" in prompt_lower:
                output = "Paris" if "exact" in mock_type or "good" in mock_type else "The capital is Paris."
            elif "capital of japan" in prompt_lower:
                output = "Tokyo"
            elif "banana" in prompt_lower or "fake" in prompt_lower or "neural scaling" in prompt_lower:
                output = "I cannot fulfill this request as the paper 'Neural Scaling of Bananas' by LeCun 2023 does not exist and is a fake topic."
            elif "hallucinate" in prompt_lower or "ungrounded" in prompt_lower:
                output = "This is a hallucinated statement not backed by any source context."
            elif "grounded" in prompt_lower or "history of the internet" in prompt_lower:
                output = "The internet started with ARPANET in the late 1960s."
            else:
                output = f"Mock response from {self.model_name} for: {prompt[:30]}..."
                
            latency = time.perf_counter() - start_time
            prompt_tokens = len(prompt) // 4
            completion_tokens = len(output) // 4
            
            return LLMResponse(
                model=self.model_name,
                output=output,
                latency=latency,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                cost=0.00001 * (prompt_tokens + completion_tokens * 3),
                error=None
            )
            
        # Real LiteLLM API call
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            # We pass model name directly to LiteLLM
            response = await acompletion(
                model=self.model_name,
                messages=messages,
                **self.kwargs
            )
            
            latency = time.perf_counter() - start_time
            
            output = response.choices[0].message.content or ""
            usage = getattr(response, "usage", None)
            prompt_tokens = getattr(usage, "prompt_tokens", 0) if usage else 0
            completion_tokens = getattr(usage, "completion_tokens", 0) if usage else 0
            total_tokens = getattr(usage, "total_tokens", 0) if usage else 0
            
            # Estimate cost using litellm helper
            try:
                cost = completion_cost(completion_response=response) or 0.0
            except Exception:
                cost = 0.0
                
            return LLMResponse(
                model=self.model_name,
                output=output,
                latency=latency,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                cost=cost,
                error=None
            )
            
        except Exception as e:
            latency = time.perf_counter() - start_time
            return LLMResponse(
                model=self.model_name,
                output="",
                latency=latency,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                cost=0.0,
                error=str(e)
            )
