from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from typing import TypedDict, List, Dict, Optional
from llm import LLMClient
from prompts import PromptTemplates
import logging
import json
import os
from dotenv import load_dotenv
from datetime import datetime

from uuid import uuid4
import re

# Ensure logs directory exists
logs_dir = "logs"
os.makedirs(logs_dir, exist_ok=True)

# Configure logging with unique log file per run
log_filename = os.path.join(logs_dir, f"log_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    query: str
    response: str
    follow_up_questions: List[str]
    budget_estimation: str
    conversation_history: List[Dict[str, str]]
    is_project_related: Optional[bool]

class BudgetAgent:
    def __init__(self, model_provider: str = "openrouter", max_history_length: int = 10):
        load_dotenv()
        logger.info(f"Initializing BudgetAgent with model provider: {model_provider}")
        self.llm_client = LLMClient(model_provider=model_provider)
        self.prompt_templates = PromptTemplates()
        self.checkpointer = MemorySaver()
        self.graph = self._build_graph()
        self.model_provider = model_provider.lower()  # Store provider for reference
        self.max_history_length = max_history_length  # Maximum number of exchanges to keep in history

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow with memory.
        """
        logger.debug("Building LangGraph workflow")
        graph = StateGraph(AgentState)
        graph.add_node("classify_query", self._classify_query)
        graph.add_node("process_project_query", self._process_project_query)
        graph.add_node("process_general_query", self._process_general_query)
        graph.add_conditional_edges(
            "classify_query",
            self._route_query,
            {
                "project": "process_project_query",
                "general": "process_general_query",
                "end": END
            }
        )
        graph.set_entry_point("classify_query")
        logger.info("LangGraph workflow built")
        return graph.compile(checkpointer=self.checkpointer)

    def _classify_query(self, state: AgentState) -> AgentState:
        """
        Classify whether the query is project-related using a simple LLM call.
        """
        logger.info(f"Classifying query: {state['query']}")
        prompt = self.prompt_templates.get_classification_prompt(state["query"])
        llm_response = self.llm_client.generate_response(prompt, max_tokens=50)
        response_text = None

        if self.model_provider == "openrouter":
            if llm_response and isinstance(llm_response, dict) and "choices" in llm_response and llm_response["choices"]:
                response_text = llm_response["choices"][0].get("text", "").strip()
        elif self.model_provider == "gemini":
            if llm_response and isinstance(llm_response, dict) and "candidates" in llm_response and llm_response["candidates"]:
                response_text = llm_response["candidates"][0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()

        if not response_text:
            logger.error("Failed to extract response text from LLM response")
            return {**state, "is_project_related": False}

        logger.debug(f"Raw LLM response: {response_text}")  # Add this to debug the response

        # Enhanced regex to capture JSON even with surrounding text
        json_pattern = re.compile(r'(?:\{.*?"is_project_related":\s*(true|false)\s*.*?\})', re.IGNORECASE | re.DOTALL)
        match = json_pattern.search(response_text)
        is_project_related = match.group(1).lower() == "true" if match else False

        state["is_project_related"] = is_project_related
        print(f"Query classified as project-related: {is_project_related}")
        return state

    def _route_query(self, state: AgentState) -> str:
        """
        Route the query based on classification.
        """
        is_project_related = state.get("is_project_related")  # Safe access with default False
        print(f"Routing query: {is_project_related}")
        if state.get("is_project_related"):
            return "project"
        return "general"

    def _process_project_query(self, state: AgentState) -> AgentState:
        """
        Process project-related queries with memory and detailed response.
        """
        logger.info(f"Processing project query: {state['query']}")
        try:
            prompt = self.prompt_templates.get_query_prompt(state["query"], state["conversation_history"])
            llm_response = self.llm_client.generate_response(prompt, max_tokens=500)
            response_text = None

            if self.model_provider == "openrouter":
                if llm_response and isinstance(llm_response, dict) and "choices" in llm_response and llm_response["choices"]:
                    response_text = llm_response["choices"][0].get("text", "").strip()
            elif self.model_provider == "gemini":
                if llm_response and isinstance(llm_response, dict) and "candidates" in llm_response and llm_response["candidates"]:
                    response_text = llm_response["candidates"][0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()

            if not response_text:
                logger.error("Invalid or no response from LLM")
                return {
                    **state,
                    "response": "Sorry, I couldn't process your query. Please try again.",
                    "follow_up_questions": ["Please provide more details about your project requirements."] * 4,
                    "budget_estimation": "Unable to estimate budget"
                }

            logger.info(f"Raw LLM response: {response_text}")

            # Parse JSON response
            json_pattern = re.compile(r'\{.*?\}', re.DOTALL)
            json_match = json_pattern.search(response_text)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_text

            try:
                response_data = json.loads(json_str)
                if not isinstance(response_data, dict) or \
                   "response" not in response_data or \
                   "follow_up_questions" not in response_data or \
                   "budget_estimation" not in response_data:
                    logger.error("Invalid JSON structure: missing required fields")
                    return {
                        **state,
                        "response": "Invalid response format from model.",
                        "follow_up_questions": ["Please provide more details about your project requirements."] * 4,
                        "budget_estimation": "Unable to estimate budget due to invalid response format."
                    }

                response = response_data["response"].strip()
                questions = response_data["follow_up_questions"]
                budget = response_data["budget_estimation"].strip()

                # sentence_count = len([s for s in response.split('.') if s.strip()])
                # if not (5 <= sentence_count <= 6):
                #     logger.warning(f"Response has {sentence_count} sentences, expected 5-6")
                #     response = "Invalid response length from model."

                # if not isinstance(questions, list) or not (4 <= len(questions) <= 5):
                #     logger.warning(f"LLM returned {len(questions)} follow-up questions, expected 4-5")
                #     questions = ["Please provide more details about your project requirements."] * 4

                if not response:
                    response = "No detailed response provided by the model."
                if not budget:
                    budget = "More information needed for budget estimation."

                return {
                    **state,
                    "response": response,
                    "follow_up_questions": questions[:5],
                    "budget_estimation": budget,
                    "conversation_history": state["conversation_history"] + [{"query": state["query"], "response": response}]
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {str(e)}")
                error_response = "Invalid response format from model."
                return {
                    **state,
                    "response": error_response,
                    "follow_up_questions": ["Please provide more details about your project requirements."] * 4,
                    "budget_estimation": "Unable to estimate budget due to invalid response format.",
                    "conversation_history": state["conversation_history"] + [{"query": state["query"], "response": error_response}]
                }
        except Exception as e:
            logger.error(f"Unexpected error in process_project_query: {str(e)}")
            error_response = "An unexpected error occurred"
            return {
                **state,
                "response": error_response,
                "follow_up_questions": ["Please provide more details about your project requirements."] * 4,
                "budget_estimation": "Unable to estimate budget",
                "conversation_history": state["conversation_history"] + [{"query": state["query"], "response": error_response}]
            }

    def _process_general_query(self, state: AgentState) -> AgentState:
        """
        Process general queries with a simple LLM call.
        """
        logger.info(f"Processing general query: {state['query']}")
        try:
            prompt = self.prompt_templates.get_general_prompt(state["query"])
            llm_response = self.llm_client.generate_response(prompt, max_tokens=200)
            response_text = None

            if self.model_provider == "openrouter":
                if llm_response and isinstance(llm_response, dict) and "choices" in llm_response and llm_response["choices"]:
                    response_text = llm_response["choices"][0].get("text", "").strip()
            elif self.model_provider == "gemini":
                if llm_response and isinstance(llm_response, dict) and "candidates" in llm_response and llm_response["candidates"]:
                    response_text = llm_response["candidates"][0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()

            if not response_text:
                logger.error("Failed to extract response text from LLM response")
                error_response = "Sorry, I couldn't process your query."
                return {
                    **state,
                    "response": error_response,
                    "follow_up_questions": [],
                    "budget_estimation": "",
                    "conversation_history": state["conversation_history"] + [{"query": state["query"], "response": error_response}]
                }

            # Update conversation history with current exchange
            return {
                **state,
                "response": response_text,
                "follow_up_questions": [],
                "budget_estimation": "",
                "conversation_history": state["conversation_history"] + [{"query": state["query"], "response": response_text}]
            }
        except Exception as e:
            logger.error(f"Error processing general query: {str(e)}")
            error_response = "Sorry, I couldn't process your query."
            return {
                **state,
                "response": error_response,
                "follow_up_questions": [],
                "budget_estimation": "",
                "conversation_history": state["conversation_history"] + [{"query": state["query"], "response": error_response}]
            }
            
    def build_prompt_with_history(history: List[Dict], current_query: str, task_instruction: str = "") -> str:
        """
        Builds a prompt including memory and current user query.
        Optionally include task_instruction (e.g., 'classify intent', 'answer as assistant').
        """
        history_prompt = "\n".join([
            f"User: {h['query']}\nAssistant: {h['response']}"
            for h in history
        ])

        prompt = f"""
        You are a helpful AI assistant.

        {task_instruction}

        Conversation so far:
        {history_prompt}

        Now the user says: "{current_query}"
        Respond appropriately.
        """.strip()

        return prompt


    def run(self, query: str, thread_id: str = "default") -> Dict[str, any]:
        """
        Run the agent with the given query and thread_id for memory persistence.
        """
        logger.info(f"Running agent with query: {query} and thread_id: {thread_id}")
        try:
            config = {
                "configurable": {
                    "thread_id": thread_id,
                    "checkpoint_ns": "default_ns"
                }
            }

            # Try to load previous conversation history
            conversation_history = []
            try:
                # Attempt to retrieve the checkpoint
                checkpoint_tuple = self.checkpointer.get(config)
                logger.debug(f"Retrieved checkpoint: {json.dumps(checkpoint_tuple, default=str) if checkpoint_tuple else 'None'}")
                
                if checkpoint_tuple:
                    try:
                        # Handle both CheckpointTuple and plain dict
                        if hasattr(checkpoint_tuple, 'get') and callable(checkpoint_tuple.get):
                            checkpoint_data = checkpoint_tuple.get("checkpoint", checkpoint_tuple)
                        elif isinstance(checkpoint_tuple, dict):
                            checkpoint_data = checkpoint_tuple.get("checkpoint", checkpoint_tuple)
                        else:
                            # Try to access checkpoint attribute directly
                            checkpoint_data = getattr(checkpoint_tuple, "checkpoint", checkpoint_tuple)

                        # Extract conversation history using multiple fallback strategies
                        extracted = False
                        
                        # Strategy 1: Check if entire state was stored directly (not under "__start__")
                        if isinstance(checkpoint_data, dict) and "query" in checkpoint_data:
                            # This is a full result object
                            logger.info("Found full result object in checkpoint")
                            conversation_history = checkpoint_data.get("conversation_history", [])
                            logger.info(f"Retrieved memory with {len(conversation_history)} exchanges.")
                            extracted = True
                        
                        # Strategy 2: Standard LangGraph checkpoint format
                        if not extracted and isinstance(checkpoint_data, dict):
                            channel_values = checkpoint_data.get("channel_values", {})
                            if isinstance(channel_values, dict) and "__start__" in channel_values:
                                previous_state = channel_values["__start__"]
                                if isinstance(previous_state, dict) and "conversation_history" in previous_state:
                                    conversation_history = previous_state.get("conversation_history", [])
                                    logger.info(f"Retrieved memory from __start__ with {len(conversation_history)} exchanges.")
                                    extracted = True
                        
                        # Strategy 3: Search for conversation_history in any channel_values
                        if not extracted and isinstance(checkpoint_data, dict):
                            channel_values = checkpoint_data.get("channel_values", {})
                            if isinstance(channel_values, dict):
                                logger.warning("No '__start__' key found in checkpoint channel_values or it doesn't contain conversation_history.")
                                # Try to extract conversation history from other parts of the checkpoint
                                for key, value in channel_values.items():
                                    if isinstance(value, dict) and "conversation_history" in value:
                                        conversation_history = value.get("conversation_history", [])
                                        logger.info(f"Recovered memory from alternative key '{key}' with {len(conversation_history)} exchanges.")
                                        extracted = True
                                        break
                        
                        # Strategy 4: Direct search in checkpoint_data for any conversation_history
                        if not extracted and isinstance(checkpoint_data, dict):
                            # Last resort: recursively search for conversation_history in the checkpoint_data
                            def find_conversation_history(data, depth=0, max_depth=3):
                                if depth > max_depth:
                                    return None
                                if isinstance(data, dict):
                                    if "conversation_history" in data and isinstance(data["conversation_history"], list):
                                        return data["conversation_history"]
                                    for k, v in data.items():
                                        result = find_conversation_history(v, depth + 1, max_depth)
                                        if result is not None:
                                            return result
                                return None
                            
                            found_history = find_conversation_history(checkpoint_data)
                            if found_history:
                                conversation_history = found_history
                                logger.info(f"Recovered memory through deep search with {len(conversation_history)} exchanges.")
                                extracted = True
                        
                        # If we still couldn't extract conversation history, log a warning
                        if not extracted:
                            logger.warning("Could not extract conversation history from checkpoint using any strategy.")
                            logger.debug(f"Checkpoint structure: {json.dumps(checkpoint_data, default=str)}")
                            conversation_history = []
                    except Exception as e:
                        logger.warning(f"Error while reading checkpoint: {str(e)}")

                else:
                    logger.info("No previous checkpoint found.")
            except Exception as e:
                logger.warning(f"Error while reading checkpoint: {str(e)}")

            # Prepare initial state
            initial_state = {
                "query": query,
                "response": "",
                "follow_up_questions": [],
                "budget_estimation": "",
                "conversation_history": conversation_history
            }

            # Run the LangGraph workflow
            result = self.graph.invoke(initial_state, config=config)

            # Save the final updated state (including the response)
            try:
                # Validate result structure before saving
                if not isinstance(result, dict):
                    logger.warning(f"Result is not a dictionary: {type(result)}")
                    result = {
                        "query": query,
                        "response": str(result),
                        "follow_up_questions": [],
                        "budget_estimation": "",
                        "conversation_history": conversation_history
                    }
                
                # Ensure conversation_history exists in the result
                if "conversation_history" not in result:
                    logger.warning("conversation_history missing from result, adding empty list")
                    result["conversation_history"] = []
                
                checkpoint_id = str(uuid4())  # create a unique ID for the saved checkpoint
                
                # Create a properly structured checkpoint
                checkpoint_data = {
                    "id": checkpoint_id,
                    "ts": datetime.utcnow().isoformat(),
                    "v": 4,
                    "channel_values": {
                        "__start__": result  
                    },
                    "channel_versions": {
                        "__start__": "00000000000000000000000000000001.0.0"
                    },
                    "versions_seen": {
                        "__input__": {}
                    }
                }
                
                # Log checkpoint structure for debugging
                logger.debug(f"Saving checkpoint with structure: {json.dumps(checkpoint_data, default=str)}")
                
                self.checkpointer.put(
                    config,   # config with thread_id and checkpoint_ns
                    checkpoint_data,
                    {},  # metadata
                    {}   # new_versions
                )


                logger.info("Checkpoint successfully saved.")
            except Exception as e:
                logger.warning(f"Error while saving checkpoint: {str(e)}")

            logger.info(f"Final agent result: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result

        except Exception as e:
            logger.error(f"Error running agent: {str(e)}")
            return {
                "query": query,
                "response": "An error occurred while processing your request",
                "follow_up_questions": ["Please provide more details about your project requirements."] * 4,
                "budget_estimation": "Unable to estimate budget",
                "conversation_history": []
            }

