from typing import List, Dict

class PromptTemplates:
    @staticmethod
    def get_query_prompt(query: str) -> str:
        """
        Generate prompt for processing user query and suggesting follow-up questions.
        """
        return f"""
        You are a professional budget estimation assistant. Given the user query below, provide a clear and concise response, suggest 3 relevant follow-up questions to gather more details, and include a preliminary budget estimation if applicable.

        User Query: {query}

        Response Format:
        - Answer: [Your response to the query]
        - Follow-up Questions:
          1. [Question 1]
          2. [Question 2]
          3. [Question 3]
        - Budget Estimation: [Preliminary budget range or note if more details are needed]
        """

    @staticmethod
    def get_budget_refinement_prompt(query: str, context: List[Dict[str, str]]) -> str:
        """
        Generate prompt for refining budget estimation based on previous context.
        """
        context_str = "\n".join([f"Q: {item['query']}\nA: {item['response']}" for item in context])
        return f"""
        Based on the conversation history below, refine the budget estimation for the user's project or query.

        Conversation History:
        {context_str}

        Current Query: {query}

        Provide a refined budget estimation and explain any assumptions made.
        Response Format:
        - Refined Budget: [Budget range or specific amount]
        - Assumptions: [List of assumptions]
        """