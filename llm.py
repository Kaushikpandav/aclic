import os
import logging
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from datetime import datetime

# Ensure logs directory exists
logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)

# Configure logging with unique log file per run
log_filename = os.path.join(logs_dir, f"log_llm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, model_provider: str = ""):
        load_dotenv()
        self.model_provider = model_provider.lower()
        logger.info(f"Initializing LLMClient with model provider: {self.model_provider}")
        
        if self.model_provider == "openrouter":
            self.api_key = os.getenv("OPENROUTER_API_KEY")
            self.api_url = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1")
            self.model = "qwen/qwen3-32b:free"
            if not self.api_key:
                logger.error("OPENROUTER_API_KEY not found in .env file")
                raise ValueError("OPENROUTER_API_KEY is required for OpenRouter")
        elif self.model_provider == "gemini":
            self.api_key = os.getenv("GEMINI_API_KEY")
            print(f"Gemini API Key: {self.api_key}")  # Debugging line to check API key
            self.api_url = os.getenv("GEMINI_API_URL", "https://generativelanguage.googleapis.com/v1")
            self.model = "gemini-2.0-flash"  # Adjust based on available Gemini models
            if not self.api_key:
                logger.error("GEMINI_API_KEY not found in .env file")
                raise ValueError("GEMINI_API_KEY is required for Gemini")
        else:
            logger.error(f"Invalid model provider: {model_provider}")
            raise ValueError("Model provider must be 'openrouter' or 'gemini'")

    def generate_response(self, prompt: str, max_tokens: int = 300) -> Optional[Dict[str, Any]]:
        """
        Generate a response from the specified model provider (OpenRouter or Gemini).
        """
        logger.debug(f"Sending prompt to {self.model_provider} at {self.api_url} with model {self.model}: {prompt[:50]}...")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        if self.model_provider == "openrouter":
            payload = {
                "model": self.model,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            url = f"{self.api_url}/chat/completions"
        elif self.model_provider == "gemini":
             headers = {
                "Content-Type": "application/json"
             }
             payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "maxOutputTokens": max_tokens,
                    "temperature": 0.7
                },
                "safetySettings": [
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                ]
             }
             url = f"{os.getenv("GEMINI_API_URL")}/models/{"gemini-2.0-flash"}:generateContent?key={os.getenv("GEMINI_API_KEY")}"

        logger.debug(f"Request payload: {payload}")

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            response_data = response.json()
            logger.info(f"LLM response size: {len(response.text)} bytes")
            logger.debug(f"LLM response: {response_data}")

            if self.model_provider == "openrouter":
                if not isinstance(response_data, dict) or "choices" not in response_data or not response_data["choices"]:
                    logger.error("Invalid OpenRouter response structure: missing 'choices' or invalid format")
                    return None
                if not isinstance(response_data["choices"], list) or not response_data["choices"][0].get("text"):
                    logger.error("Invalid OpenRouter response: 'choices' is not a list or missing 'text'")
                    return None
                return response_data
            elif self.model_provider == "gemini":
                if not isinstance(response_data, dict) or "candidates" not in response_data or not response_data["candidates"]:
                    logger.error("Invalid Gemini response structure: missing 'candidates' or invalid format")
                    return None
                if not isinstance(response_data["candidates"], list) or not response_data["candidates"][0].get("content", {}).get("parts", [{}])[0].get("text"):
                    logger.error("Invalid Gemini response: 'candidates' is not a list or missing 'text'")
                    return None
                return response_data

            return response_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to call {self.model_provider} API: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in {self.model_provider} LLM call: {str(e)}")
            return None