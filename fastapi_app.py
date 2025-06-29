from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from agent import BudgetAgent
import logging
import uvicorn
import os 

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Agentic Budget Bot API")

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    response: str
    follow_up_questions: list
    budget_estimation: str

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred", "error": str(exc)}
    )

@app.get("/")
async def root():
    """
    Root endpoint to provide a welcome message.
    """
    return {
        "message": "Welcome to the Agentic Budget Bot API",
        "documentation": "/docs",
        "endpoint": "POST /query to submit a query"
    }

@app.get("/favicon.ico")
async def favicon():
    """
    Handle favicon requests to prevent 404 errors.
    """
    return JSONResponse(status_code=204, content={})

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a query and return response with follow-up questions and budget estimation.
    """
    try:
        # Pass the model provider from .env or default to 'openrouter'
        model_provider = os.getenv("MODEL_PROVIDER", "openrouter")
        agent = BudgetAgent(model_provider=model_provider)
        result = agent.run(request.query)
        return QueryResponse(
            response=result["response"],
            follow_up_questions=result["follow_up_questions"],
            budget_estimation=result["budget_estimation"]
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)