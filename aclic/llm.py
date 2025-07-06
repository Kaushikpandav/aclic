import os
import logging
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, model_provider: str = "openrouter"):
        load_dotenv()
        self.model_provider = model_provider.lower()
        
        if self.model_provider == "openrouter":
            self.api_key = os.getenv("OPENROUTER_API_KEY")
            self.api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
            self.model = "qwen/qwen3-32b:free"  # Qwen 3 32B for OpenRouter
            if not self.api_key:
                logger.error("OPENROUTER_API_KEY not found in .env file")
                raise ValueError("OPENROUTER_API_KEY is required for OpenRouter")
        elif self.model_provider == "gemini":
            self.api_key = os.getenv("GEMINI_API_KEY")
            self.api_url = os.getenv("GEMINI_API_URL", "https://api.gemini.com/v1")  # Adjust based on actual Gemini API endpoint
            self.model = "gemini-2.5"  # Gemini 2.5
            if not self.api_key:
                logger.error("GEMINI_API_KEY not found in .env file")
                raise ValueError("GEMINI_API_KEY is required for Gemini")
        else:
            logger.error(f"Invalid model provider: {model_provider}")
            raise ValueError("Model provider must be 'openrouter' or 'gemini'")

    def generate_response(self, prompt: str, max_tokens: int = 300) -> Optional[Dict[str, Any]]:
        """
        Generate a response from the selected model (Qwen 3 32B via OpenRouter or Gemini 2.5).
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }

        try:
            response = requests.post(f"{self.api_url}/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            logger.info(f"LLM response size: {len(response.text)} bytes")
            return response_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call {self.model_provider} API: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in {self.model_provider} LLM call: {str(e)}")
            return None