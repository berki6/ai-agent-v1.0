import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional, List, AsyncGenerator, cast
from abc import ABC, abstractmethod

from google import genai
from google.genai import types
from google.genai.errors import APIError

from .logger import get_logger


class AIService(ABC):
    """Abstract base class for AI services"""

    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> str:
        pass

    @abstractmethod
    async def analyze_code(self, code: str, **kwargs) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def stream_text(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream text generation"""
        pass


class GeminiService(AIService):
    """Gemini API service implementation using official google-genai library"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.logger = get_logger(__name__)
        self._client: Optional[genai.Client] = None
        self._thread_pool = ThreadPoolExecutor(max_workers=4)

        if self.api_key:
            try:
                self._client = genai.Client(api_key=self.api_key)
                self.logger.info("Gemini client initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini client: {e}")
                self._client = None
        else:
            self.logger.warning(
                "Gemini API key not found. Set GEMINI_API_KEY environment variable."
            )

    async def generate_text(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash-exp",
        max_tokens: int = 2048,
        **kwargs,
    ) -> str:
        """Generate text using Gemini API"""
        if not self._client:
            raise ValueError("Gemini client not initialized. Check API key.")

        # Cast to ensure type checker knows it's not None
        client = cast(genai.Client, self._client)

        def _sync_generate():
            try:
                config = types.GenerateContentConfig(
                    max_output_tokens=max_tokens, **kwargs
                )
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                return response.text if response.text is not None else ""
            except APIError as e:
                self.logger.error(f"Gemini API error: {e}")
                raise
            except Exception as e:
                self.logger.error(f"Unexpected error in text generation: {e}")
                raise

        loop = asyncio.get_running_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(self._thread_pool, _sync_generate), timeout=60.0
            )
            return result
        except asyncio.TimeoutError:
            self.logger.error("Gemini text generation timeout")
            raise TimeoutError("Text generation timed out")
        except Exception as e:
            self.logger.error(f"Async text generation failed: {e}")
            raise

    async def analyze_code(self, code: str, **kwargs) -> Dict[str, Any]:
        """Analyze code using Gemini API"""
        prompt = f"Analyze the following code and provide insights:\n\n{code}"
        analysis = await self.generate_text(prompt, **kwargs)
        return {"analysis": analysis}

    async def stream_text(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash-exp",
        max_tokens: int = 2048,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream text generation from Gemini API"""
        if not self._client:
            yield "Error: Gemini client not initialized"
            return

        # Cast to ensure type checker knows it's not None
        client = cast(genai.Client, self._client)

        try:
            config = types.GenerateContentConfig(max_output_tokens=max_tokens, **kwargs)
            stream = client.models.generate_content_stream(
                model=model,
                contents=prompt,
                config=config,
            )
            for chunk in stream:
                text = chunk.text if chunk.text is not None else ""
                yield text
        except APIError as e:
            self.logger.error(f"Gemini streaming API error: {e}")
            yield f"Error: {e}"
        except Exception as e:
            self.logger.error(f"Unexpected streaming error: {e}")
            yield f"Error: {e}"


class AIUtils:
    """Utility class for AI operations"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.services: Dict[str, AIService] = {}

        # Initialize default Gemini service
        self.services["gemini"] = GeminiService()

    def get_service(self, name: str = "gemini") -> Optional[AIService]:
        """Get an AI service by name"""
        return self.services.get(name)

    def add_service(self, name: str, service: AIService):
        """Add a custom AI service"""
        self.services[name] = service

    async def generate_text(
        self, prompt: str, service: str = "gemini", **kwargs
    ) -> str:
        """Convenience method for text generation"""
        svc = self.get_service(service)
        if not svc:
            raise ValueError(f"AI service '{service}' not found")
        return await svc.generate_text(prompt, **kwargs)

    async def analyze_code(
        self, code: str, service: str = "gemini", **kwargs
    ) -> Dict[str, Any]:
        """Convenience method for code analysis"""
        svc = self.get_service(service)
        if not svc:
            raise ValueError(f"AI service '{service}' not found")
        return await svc.analyze_code(code, **kwargs)

    async def stream_text(
        self, prompt: str, service: str = "gemini", **kwargs
    ) -> AsyncGenerator[str, None]:
        """Convenience method for streaming text generation"""
        svc = self.get_service(service)
        if not svc:
            raise ValueError(f"AI service '{service}' not found")
        gen = await svc.stream_text(prompt, **kwargs)
        async for chunk in gen:
            yield chunk
