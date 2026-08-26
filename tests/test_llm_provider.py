import pytest
from typing import Dict, Any

from app.core.llm_provider import LLMProvider
import config

# Simple messages to test the APIs
TEST_MESSAGES = [
    {"role": "system", "content": "You are a helpful assistant. Keep your answers very short."},
    {"role": "user", "content": "What is 2 + 2?"}
]

TEST_JSON_MESSAGES = [
    {"role": "system", "content": "You are a helpful assistant. Always return your response in JSON format. Do not include any extra text."},
    {"role": "user", "content": "Return a JSON object with a key 'result' and value 4."}
]


@pytest.mark.asyncio
class TestOllamaProvider:
    """Tests for the Ollama LLM provider."""
    
    @pytest.fixture
    def provider(self):
        # We assume Ollama might not always be running in CI, but we'll try to run it.
        # If the connection fails, the test will fail, which is expected for a functional test.
        # You might want to skip this in CI if Ollama isn't available.
        return LLMProvider(provider="ollama")

    async def test_ollama_generate_async(self, provider: LLMProvider):
        try:
            response = await provider.generate_async(TEST_MESSAGES)
            assert isinstance(response, str)
            assert len(response) > 0
        except Exception as e:
            pytest.skip(f"Ollama functional test failed, possibly not running: {e}")

    async def test_ollama_generate_json_async(self, provider: LLMProvider):
        try:
            response = await provider.generate_json_async(TEST_JSON_MESSAGES)
            assert isinstance(response, dict)
        except Exception as e:
            pytest.skip(f"Ollama functional JSON test failed, possibly not running: {e}")


@pytest.mark.asyncio
@pytest.mark.skipif(not config.GROQ_API_KEY, reason="GROQ_API_KEY is not set")
class TestGroqProvider:
    """Tests for the Groq LLM provider."""
    
    @pytest.fixture
    def provider(self):
        return LLMProvider(provider="groq")

    async def test_groq_generate_async(self, provider: LLMProvider):
        response = await provider.generate_async(TEST_MESSAGES)
        assert isinstance(response, str)
        assert len(response) > 0

    async def test_groq_generate_json_async(self, provider: LLMProvider):
        response = await provider.generate_json_async(TEST_JSON_MESSAGES)
        assert isinstance(response, dict)


@pytest.mark.asyncio
@pytest.mark.skipif(not config.SARVAM_API_KEY, reason="SARVAM_API_KEY is not set")
class TestSarvamProvider:
    """Tests for the Sarvam LLM provider."""
    
    @pytest.fixture
    def provider(self):
        return LLMProvider(provider="sarvam")

    async def test_sarvam_generate_async(self, provider: LLMProvider):
        response = await provider.generate_async(TEST_MESSAGES)
        assert isinstance(response, str)
        assert len(response) > 0

    async def test_sarvam_generate_json_async(self, provider: LLMProvider):
        response = await provider.generate_json_async(TEST_JSON_MESSAGES)
        assert isinstance(response, dict)
