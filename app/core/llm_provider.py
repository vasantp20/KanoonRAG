import json
import httpx
import asyncio
from typing import List, Dict, Optional, Any

import config

class LLMProvider:
    """Factory and Base Class for LLM API Providers."""
    
    def __new__(cls, provider: Optional[str] = None, model: Optional[str] = None):
        if cls is not LLMProvider:
            return super().__new__(cls)
            
        provider_name = provider or getattr(config, "PRIMARY_LLM", "ollama")
        
        if provider_name == "groq":
            return super().__new__(GroqProvider)
        elif provider_name == "ollama":
            return super().__new__(OllamaProvider)
        elif provider_name == "sarvam":
            return super().__new__(SarvamProvider)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")

    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        pass

    async def generate_async(self, messages: List[Dict[str, str]], telemetry_ctx: Optional[Dict] = None) -> str:
        raise NotImplementedError

    async def generate_json_async(self, messages: List[Dict[str, str]], telemetry_ctx: Optional[Dict] = None) -> dict:
        raise NotImplementedError

    def get_langchain_model(self):
        raise NotImplementedError

    async def close(self):
        pass


class GroqProvider(LLMProvider):
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = "groq"
        self.model = model or config.GROQ_MODEL
        from groq import AsyncGroq
        self.client = AsyncGroq(api_key=config.GROQ_API_KEY)

    async def close(self):
        await self.client.close()

    async def generate_async(self, messages: List[Dict[str, str]], telemetry_ctx: Optional[Dict] = None) -> str:
        params = {
            "messages": messages,
            "model": self.model,
            "temperature": config.GROQ_TEMPERATURE,
            "max_tokens": config.GROQ_MAX_TOKENS,
        }
        response = await self.client.chat.completions.create(**params)
        
        if telemetry_ctx and hasattr(response, 'usage') and response.usage:
            from app.core.telemetry import log_llm_usage
            usage = response.usage
            log_llm_usage(
                telemetry_ctx.get('query_uuid'),
                telemetry_ctx.get('query'),
                telemetry_ctx.get('step'),
                getattr(usage, 'prompt_tokens', 0),
                getattr(usage, 'completion_tokens', 0),
                self.provider
            )
            
        return response.choices[0].message.content

    async def generate_json_async(self, messages: List[Dict[str, str]], telemetry_ctx: Optional[Dict] = None) -> dict:
        params = {
            "messages": messages,
            "model": self.model,
            "temperature": config.GROQ_TEMPERATURE,
            "max_tokens": config.GROQ_MAX_TOKENS,
            "response_format": {"type": "json_object"}
        }
        try:
            response = await self.client.chat.completions.create(**params)
            
            if telemetry_ctx and hasattr(response, 'usage') and response.usage:
                from app.core.telemetry import log_llm_usage
                usage = response.usage
                log_llm_usage(
                    telemetry_ctx.get('query_uuid'),
                    telemetry_ctx.get('query'),
                    telemetry_ctx.get('step'),
                    getattr(usage, 'prompt_tokens', 0),
                    getattr(usage, 'completion_tokens', 0),
                    self.provider
                )

            content = response.choices[0].message.content
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            print(f"Error parsing JSON from groq: {e}")
            return {}

    def get_langchain_model(self):
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                model=self.model,
                api_key=config.GROQ_API_KEY,
                temperature=0
            )
        except ImportError:
            raise ImportError("Please install langchain-groq (`pip install langchain-groq`) to use Groq with Ragas.")


class OllamaProvider(LLMProvider):
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = "ollama"
        self.model = model or config.OLLAMA_MODEL
        self.http_client = httpx.AsyncClient(timeout=120.0)
        
    async def close(self):
        await self.http_client.aclose()

    async def generate_async(self, messages: List[Dict[str, str]], telemetry_ctx: Optional[Dict] = None) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": config.OLLAMA_TEMPERATURE,
                "num_predict": config.OLLAMA_MAX_TOKENS
            }
        }
        response = await self.http_client.post(
            f"{config.OLLAMA_BASE_URL.rstrip('/')}/api/chat",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()  
        
        if telemetry_ctx:
            from app.core.telemetry import log_llm_usage
            log_llm_usage(
                telemetry_ctx.get('query_uuid'),
                telemetry_ctx.get('query'),
                telemetry_ctx.get('step'),
                data.get('prompt_eval_count', 0),
                data.get('eval_count', 0),
                self.provider
            )
            
        return data["message"]["content"]

    async def generate_json_async(self, messages: List[Dict[str, str]], telemetry_ctx: Optional[Dict] = None) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": config.OLLAMA_TEMPERATURE,
                "num_predict": config.OLLAMA_MAX_TOKENS
            }
        }
        try:
            response = await self.http_client.post(
                f"{config.OLLAMA_BASE_URL.rstrip('/')}/api/chat",
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()  
            
            if telemetry_ctx:
                from app.core.telemetry import log_llm_usage
                log_llm_usage(
                    telemetry_ctx.get('query_uuid'),
                    telemetry_ctx.get('query'),
                    telemetry_ctx.get('step'),
                    data.get('prompt_eval_count', 0),
                    data.get('eval_count', 0),
                    self.provider
                )
                
            content = data["message"]["content"]
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            print(f"Error parsing JSON from ollama: {e}")
            print(f"Raw output: {content[:500] if 'content' in locals() else 'None'}")
            return {}

    def get_langchain_model(self):
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=self.model,
            base_url=config.OLLAMA_BASE_URL,
            temperature=0
        )


class SarvamProvider(LLMProvider):
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        self.provider = "sarvam"
        self.model = model or config.SARVAM_MODEL
        from sarvamai import SarvamAI
        # Initialize standard client
        self.client = SarvamAI(api_subscription_key=config.SARVAM_API_KEY)

    async def generate_async(self, messages: List[Dict[str, str]], telemetry_ctx: Optional[Dict] = None) -> str:
        def _call():
            response = self.client.chat.completions(
                messages=messages,
                model=self.model,
                max_tokens=4096,
            )
            
            content = ""
            if hasattr(response, 'choices'):
                content = response.choices[0].message.content
                content = content if content is not None else ""
            elif isinstance(response, dict) and 'choices' in response:
                content = response['choices'][0]['message'].get('content', '')
                if isinstance(content, dict):
                    content = content.get('content', '')
                content = content if content is not None else ""
            else:
                content = str(response)
            return content, response

        content, response = await asyncio.to_thread(_call)
        
        if telemetry_ctx:
            input_tokens, output_tokens = 0, 0
            if hasattr(response, 'usage') and response.usage:
                input_tokens = getattr(response.usage, 'prompt_tokens', 0)
                output_tokens = getattr(response.usage, 'completion_tokens', 0)
            elif isinstance(response, dict) and 'usage' in response:
                input_tokens = response['usage'].get('prompt_tokens', 0)
                output_tokens = response['usage'].get('completion_tokens', 0)
                
            from app.core.telemetry import log_llm_usage
            log_llm_usage(
                telemetry_ctx.get('query_uuid'),
                telemetry_ctx.get('query'),
                telemetry_ctx.get('step'),
                input_tokens,
                output_tokens,
                self.provider
            )

        return content

    async def generate_json_async(self, messages: List[Dict[str, str]], telemetry_ctx: Optional[Dict] = None) -> dict:
        def _call_json():
            try:
                response = self.client.chat.completions(
                    messages=messages,
                    model=self.model,
                    max_tokens=4096,
                )
                print(f"DEBUG SARVAM RAW RESPONSE: {response}")
                
                content = ""
                if hasattr(response, 'choices'):
                    content = response.choices[0].message.content
                    if content is None:
                        print("DEBUG SARVAM CONTENT IS EXPLICITLY None!")
                        content = ""
                elif isinstance(response, dict) and 'choices' in response:
                    content = response['choices'][0]['message'].get('content', '')
                    if content is None:
                        content = ""
                else:
                    content = str(response)
                return content, response
            except Exception as e:
                print(f"DEBUG SARVAM EXCEPTION: {e}")
                return "", None

        content, response = await asyncio.to_thread(_call_json)      
        if not content:
            print("Error: Sarvam returned empty content.")
            return {}
            
        if telemetry_ctx and response:
            input_tokens, output_tokens = 0, 0
            if hasattr(response, 'usage') and response.usage:
                input_tokens = getattr(response.usage, 'prompt_tokens', 0)
                output_tokens = getattr(response.usage, 'completion_tokens', 0)
            elif isinstance(response, dict) and 'usage' in response:
                input_tokens = response['usage'].get('prompt_tokens', 0)
                output_tokens = response['usage'].get('completion_tokens', 0)
                
            from app.core.telemetry import log_llm_usage
            log_llm_usage(
                telemetry_ctx.get('query_uuid'),
                telemetry_ctx.get('query'),
                telemetry_ctx.get('step'),
                input_tokens,
                output_tokens,
                self.provider
            )
            
        try:
            content = content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            print(f"Error parsing JSON from sarvam: {e}")
            print(f"Raw output: {content[:500]}")
            return {}

    def get_langchain_model(self):
        try:
            from langchain_openai import ChatOpenAI
            
            class PatchedChatOpenAI(ChatOpenAI):
                def _generate(self, *args, **kwargs):
                    result = super()._generate(*args, **kwargs)
                    for gen in result.generations:
                        if gen.generation_info is None:
                            gen.generation_info = {}
                        gen.generation_info["finish_reason"] = "stop"
                    return result

                async def _agenerate(self, *args, **kwargs):
                    result = await super()._agenerate(*args, **kwargs)
                    for gen in result.generations:
                        if gen.generation_info is None:
                            gen.generation_info = {}
                        gen.generation_info["finish_reason"] = "stop"
                    return result

            return PatchedChatOpenAI(
                model=self.model,
                api_key=config.SARVAM_API_KEY,
                base_url=config.SARVAM_BASE_URL.replace("/chat/completions", ""),
                default_headers={"api-subscription-key": config.SARVAM_API_KEY},
                temperature=0,
                max_tokens=4096
            )
        except ImportError:
            raise ImportError("Please install langchain-openai to use Sarvam API with Ragas.")
