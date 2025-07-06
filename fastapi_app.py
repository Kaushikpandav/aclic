from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent import BudgetAgent
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

# Ensure logs directory exists
logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)

# Configure logging with unique log file per run
log_filename = os.path.join(logs_dir, f"log_fastapi_app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agentic Budget Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a single BudgetAgent instance at the application level
model_provider = os.getenv("MODEL_PROVIDER")
logger.info(f"Initializing global BudgetAgent with model provider: {model_provider}")
budget_agent = BudgetAgent(model_provider=model_provider)

class QueryRequest(BaseModel):
    message: str

class QueryResponse(BaseModel):
    response: str
    follow_up_questions: list
    budget_estimation: str

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error at {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred", "error": str(exc)}
    )

@app.get("/")
async def root():
    """
    Root endpoint to provide a welcome message.
    """
    logger.info("Received request to root endpoint")
    response = {
        "message": "Welcome to the Agentic Budget Bot API",
        "documentation": "/docs",
        "endpoint": "POST /query to submit a query"
    }
    logger.debug(f"Root endpoint response: {response}")
    return response

@app.get("/favicon.ico")
async def favicon():
    """
    Handle favicon requests to prevent 404 errors.
    """
    logger.info("Received request for favicon")
    return JSONResponse(status_code=204, content={})

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, x_thread_id: str = Header(default="default")):
    """
    Process a query and return response with follow-up questions and budget estimation.
    """
    logger.info(f"Processing query: {request.message} with thread_id: {x_thread_id}")
    try:
        # Use the global budget_agent instance instead of creating a new one
        result = budget_agent.run(request.message, thread_id=x_thread_id)
        logger.info(f"Query response: {result}")
        return QueryResponse(
            response=result["response"],
            follow_up_questions=result["follow_up_questions"],
            budget_estimation=result["budget_estimation"]
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")