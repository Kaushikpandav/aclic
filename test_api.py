# import pytest
# import httpx
# from fastapi import status
# import logging
# from datetime import datetime
# import os

# # Ensure logs directory exists
# logs_dir = "logs"
# os.makedirs(logs_dir, exist_ok=True)

# # Configure logging with unique log file per run
# log_filename = os.path.join(logs_dir, f"log_test_api_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler(log_filename, encoding='utf-8'),
#         logging.StreamHandler()
#     ]
# )
# logger = logging.getLogger(__name__)

# @pytest.mark.asyncio
# async def test_root_endpoint():
#     logger.info("Starting test_root_endpoint")
#     async with httpx.AsyncClient() as client:
#         response = await client.get("http://localhost:8000/")
#         logger.debug(f"Root endpoint response status: {response.status_code}")
#         assert response.status_code == status.HTTP_200_OK
#         data = response.json()
#         logger.info(f"Root endpoint response: {data}")
#         assert "message" in data
#         assert data["message"] == "Welcome to the Agentic Budget Bot API"
#         assert "documentation" in data
#         assert "endpoint" in data
#         logger.info("test_root_endpoint passed")

# @pytest.mark.asyncio
# async def test_favicon_endpoint():
#     logger.info("Starting test_favicon_endpoint")
#     async with httpx.AsyncClient() as client:
#         response = await client.get("http://localhost:8000/favicon.ico")
#         logger.debug(f"Favicon endpoint response status: {response.status_code}")
#         assert response.status_code == status.HTTP_204_NO_CONTENT
#         logger.info("test_favicon_endpoint passed")

# @pytest.mark.asyncio
# async def test_query_endpoint_success():
#     logger.info("Starting test_query_endpoint_success")
#     async with httpx.AsyncClient() as client:
#         payload = {"query": "What is the cost to build a small mobile app?"}
#         logger.debug(f"Sending query payload: {payload}")
#         response = await client.post("http://localhost:8000/query", json=payload)
#         logger.debug(f"Query endpoint response status: {response.status_code}")
#         assert response.status_code == status.HTTP_200_OK
#         data = response.json()
#         logger.info(f"Query endpoint response: {data}")
#         assert "response" in data
#         assert "follow_up_questions" in data
#         assert "budget_estimation" in data
#         assert isinstance(data["follow_up_questions"], list)
#         if data["response"] == "No detailed response provided by the model.":
#             logger.warning("Query endpoint returned fallback response, check LLM configuration")
#         logger.info("test_query_endpoint_success passed")

# @pytest.mark.asyncio
# async def test_query_endpoint_invalid_payload():
#     logger.info("Starting test_query_endpoint_invalid_payload")
#     async with httpx.AsyncClient() as client:
#         payload = {"invalid_key": "test"}
#         logger.debug(f"Sending invalid payload: {payload}")
#         response = await client.post("http://localhost:8000/query", json=payload)
#         logger.debug(f"Invalid payload response status: {response.status_code}")
#         assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
#         logger.info("test_query_endpoint_invalid_payload passed")

# @pytest.mark.asyncio
# async def test_query_endpoint_empty_query():
#     logger.info("Starting test_query_endpoint_empty_query")
#     async with httpx.AsyncClient() as client:
#         payload = {"query": ""}
#         logger.debug(f"Sending empty query payload: {payload}")
#         response = await client.post("http://localhost:8000/query", json=payload)
#         logger.debug(f"Empty query response status: {response.status_code}")
#         assert response.status_code == status.HTTP_200_OK  # Depends on LLM handling
#         data = response.json()
#         logger.info(f"Empty query response: {data}")
#         assert "response" in data
#         assert "follow_up_questions" in data
#         assert "budget_estimation" in data
#         if data["response"] == "No detailed response provided by the model.":
#             logger.warning("Empty query returned fallback response, check LLM configuration")
#         logger.info("test_query_endpoint_empty_query passed")
import requests
import logging
from datetime import datetime
import os
# Configure logging
logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)
log_filename = os.path.join(logs_dir, f"log_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_filename, encoding='utf-8'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# API Configuration
API_KEY = "AIzaSyCJscY_qbI8Mb-cJaJJ9zeFr7tVHUjF-xo"
API_URL = "https://generativelanguage.googleapis.com/v1beta"
MODEL = "gemini-pro"  # Adjust based on available models
def test_gemini_api(prompt: str, max_tokens: int = 200):
    logger.info(f"Testing Gemini API with prompt: {prompt[:50]}...")
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
    url = f"{API_URL}/models/{MODEL}:generateContent?key={API_KEY}"

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        response_data = response.json()
        logger.info(f"API response size: {len(response.text)} bytes")
        logger.debug(f"API response: {response_data}")
        print(f"Response: {response_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', 'No text')}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to call Gemini API: {str(e)}")
        print(f"Error: {str(e)}")
