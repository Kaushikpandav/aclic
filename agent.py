from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Optional
from llm import LLMClient
from prompts import PromptTemplates
import logging
import json
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    query: str
    response: str
    follow_up_questions: List[str]
    budget_estimation: str
    conversation_history: List[Dict[str, str]]

class BudgetAgent:
    def __init__(self, model_provider: str = "openrouter"):
        load_dotenv()
        self.llm_client = LLMClient(model_provider=model_provider)
        self.prompt_templates = PromptTemplates()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow for the agent.
        """
        graph = StateGraph(AgentState)

        graph.add_node("process_query", self._process_query)
        graph.add_node("refine_budget", self._refine_budget)

        graph.add_edge("process_query", "refine_budget")
        graph.add_edge("refine_budget", END)

        graph.set_entry_point("process_query")
        return graph.compile()

    def _process_query(self, state: AgentState) -> AgentState:
        """
        Process the initial query and generate response with follow-up questions.
        """
        try:
            prompt = self.prompt_templates.get_query_prompt(state["query"])
            llm_response = self.llm_client.generate_response(prompt)

            if not llm_response or "choices" not in llm_response or not llm_response["choices"]:
                logger.error("Invalid or no response from LLM")
                return {
                    **state,
                    "response": "Sorry, I couldn't process your query. Please try again.",
                    "follow_up_questions": [],
                    "budget_estimation": "Unable to estimate budget"
                }

            response_text = llm_response["choices"][0].get("text", "").strip()
            logger.info(f"Raw LLM response: {response_text}")

            # Parse response to extract answer, questions, and budget
            try:
                answer = ""
                questions = []
                budget = ""
                current_section = None
                lines = response_text.split("\n")
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("- Answer:"):
                        current_section = "answer"
                        answer = line.replace("- Answer:", "").strip()
                    elif line.startswith("- Follow-up Questions:"):
                        current_section = "questions"
                    elif line.startswith("- Budget Estimation:"):
                        current_section = "budget"
                        budget = line.replace("- Budget Estimation:", "").strip()
                    elif current_section == "questions" and line.startswith(("1.", "2.", "3.")):
                        questions.append(line[3:].strip())
                    elif current_section == "answer" and line:
                        answer += " " + line

                # Ensure response is not empty
                if not answer:
                    answer = "No detailed response provided by the model."
                if not questions:
                    questions = ["Please provide more details about your project requirements."]
                if not budget:
                    budget = "More information needed for budget estimation."

                parsed_response = {
                    **state,
                    "response": answer.strip(),
                    "follow_up_questions": questions[:3],  # Limit to 3 questions
                    "budget_estimation": budget.strip(),
                    "conversation_history": state["conversation_history"] + [{"query": state["query"], "response": answer.strip()}]
                }
                logger.info(f"Parsed response: {json.dumps(parsed_response, indent=2)}")
                return parsed_response
            except Exception as e:
                logger.error(f"Error parsing LLM response: {str(e)}")
                return {
                    **state,
                    "response": "Error processing response",
                    "follow_up_questions": [],
                    "budget_estimation": "Unable to estimate budget"
                }
        except Exception as e:
            logger.error(f"Unexpected error in process_query: {str(e)}")
            return {
                **state,
                "response": "An unexpected error occurred",
                "follow_up_questions": [],
                "budget_estimation": "Unable to estimate budget"
            }

    def _refine_budget(self, state: AgentState) -> AgentState:
        """
        Refine the budget estimation based on conversation history.
        """
        try:
            prompt = self.prompt_templates.get_budget_refinement_prompt(state["query"], state["conversation_history"])
            llm_response = self.llm_client.generate_response(prompt)

            if not llm_response or "choices" not in llm_response or not llm_response["choices"]:
                logger.error("Invalid or no response from LLM in refine_budget")
                return {
                    **state,
                    "budget_estimation": "Unable to refine budget estimation"
                }

            response_text = llm_response["choices"][0].get("text", "").strip()
            logger.info(f"Refined budget response: {response_text}")
            return {
                **state,
                "budget_estimation": response_text or "Unable to refine budget estimation"
            }
        except Exception as e:
            logger.error(f"Unexpected error in refine_budget: {str(e)}")
            return {
                **state,
                "budget_estimation": "Unable to refine budget estimation"
            }

    def run(self, query: str) -> Dict[str, any]:
        """
        Run the agent with the given query.
        """
        try:
            initial_state = {
                "query": query,
                "response": "",
                "follow_up_questions": [],
                "budget_estimation": "",
                "conversation_history": []
            }
            result = self.graph.invoke(initial_state)
            logger.info(f"Final agent result: {json.dumps(result, indent=2)}")
            return result
        except Exception as e:
            logger.error(f"Error running agent: {str(e)}")
            return {
                "query": query,
                "response": "An error occurred while processing your request",
                "follow_up_questions": [],
                "budget_estimation": "Unable to estimate budget",
                "conversation_history": []
            }