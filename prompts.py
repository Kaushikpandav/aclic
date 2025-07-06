from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class PromptTemplates:
    @staticmethod
    def get_classification_prompt(query: str) -> str:
        """
        Generate a prompt to classify if the query is related to a freelancing IT project.
        This assistant is designed to determine whether a query pertains to freelancing IT
        professional tasks (e.g., budget estimation, app development, web development,
        feature requirements, requirement gathering, software design, deployment, or
        technology stack discussions) or is a general inquiry (e.g., weather, jokes,
        personal questions, or non-technical topics).

        As a freelancing IT expert, you should proactively assume a query is project-related
        if it contains or implies technical terms (e.g., "development," "app," "web," "budget")
        unless clear evidence suggests otherwise (e.g., "development of a garden" or "personal
        development goals"). Your classification must be dynamic and context-aware:
        - Return 'true' if the query involves or hints at technical project aspects (e.g.,
          "development," "cost of an app," "web design timeline," or follow-ups like "add
          features").
        - Return 'false' only for explicitly non-technical queries (e.g., "tell me a joke,"
          "what’s the weather," "who is Hitesh?") or when the context is unambiguously
          non-IT (e.g., "child development").
        - Prioritize keywords like "development," "budget," "app," "web," "design,"
          "integration," "features," "requirements," "stack," "timeline," "deployment,"
          or "testing" as strong indicators of project relevance. A single keyword like
          "development" should lean toward 'true' in a freelancing IT context.
        - If the query is ambiguous but contains a technical keyword without contradiction,
          default to 'true' to support freelancing IT discussions.

        Dynamic context: Analyze the query for the following technical keywords: development,
        budget, cost, app, web, design, integration, features, requirements, stack, timeline,
        deployment, testing. The presence of any keyword strongly suggests a project-related
        query unless overridden by non-technical context (e.g., "development" with "personal"
        or "garden").

        Respond STRICTLY with a SINGLE JSON object containing ONLY the field 'is_project_related'
        with a boolean value (true or false). Do NOT include any additional text, explanations,
        or formatting outside the JSON object.

        Query: {query}

        Response Format:
        {{
          "is_project_related": true
        }}
        """
        logger.debug(f"Generating classification prompt for: {query}")
        # Dynamic context enhancement based on query keywords
        technical_keywords = ["development", "budget", "cost", "app", "web", "design", "integration",
                            "features", "requirements", "stack", "timeline", "deployment", "testing"]
        dynamic_context = "Dynamic context: The query contains the following technical keywords: " + \
                          ", ".join(keyword for keyword in technical_keywords if keyword in query.lower()) + \
                          ". The presence of any keyword (especially 'development') suggests a freelancing IT project unless contradicted by non-technical terms (e.g., 'personal,' 'garden,' 'joke')."
        if not any(keyword in query.lower() for keyword in technical_keywords):
            dynamic_context += " No technical keywords detected; lean toward 'false' unless implied context suggests IT relevance."

        prompt = f"""
        You are an expert classifier assistant with deep knowledge of freelancing IT professional tasks. Your role is to determine whether a query relates to freelancing IT projects—such as budget estimation, app development (e.g., Flutter, React Native), web development (e.g., MERN, Django), feature requirements, requirement gathering, software design, deployment, testing, or technology stack discussions—or is a general inquiry like weather updates, jokes, personal questions, or non-technical topics.

        As a freelancing IT expert, you understand that project-related queries often involve:
        - Estimating costs or budgets (e.g., "What’s the budget for a Flutter app?").
        - Discussing development processes (e.g., "How to integrate payment in an app?").
        - Gathering requirements (e.g., "What features for a web app?").
        - Technology stack selection (e.g., "MERN stack for e-commerce?").
        - Project timelines or deployment (e.g., "Timeline for web development?").

        General queries, however, include:
        - Casual or entertainment requests (e.g., "Tell me a joke," "What’s the weather?").
        - Personal or unrelated questions (e.g., "Who is Hitesh?," "What’s your favorite color?").
        - Non-technical topics (e.g., "How to cook rice?," "child development").

        Your classification must be dynamic and context-aware:
        - Return 'true' if the query involves or hints at technical project aspects, even standalone terms like "development" (implying software development in this context), "cost of an app," "web design timeline," or follow-ups like "add features."
        - Return 'false' only for explicitly non-technical queries (e.g., "tell me a joke," "what’s the time," "who is Hitesh?") or when the context is unambiguously non-IT (e.g., "personal development goals," "development of a garden").
        - Prioritize keywords like "development," "budget," "app," "web," "design," "integration," "features," "requirements," "stack," "timeline," "deployment," or "testing" as strong indicators of project relevance. A single keyword like "development" should lean toward 'true' in a freelancing IT context unless contradicted.
        - If the query is ambiguous but contains a technical keyword (e.g., "development") without non-technical modifiers, default to 'true' to support freelancing IT discussions.
        - Consider implied context: If the query follows a project-related conversation, lean toward 'true.'

        {dynamic_context}

        Respond STRICTLY with a SINGLE JSON object containing ONLY the field 'is_project_related'
        with a boolean value (true or false). Do NOT include any additional text, explanations,
        or formatting outside the JSON object.

        Query: {query}

        Response Format:
        {{
          "is_project_related": true
        }}
        """
        logger.info("Classification prompt generated")
        return prompt

    @staticmethod
    def get_query_prompt(query: str, conversation_history: List[Dict[str, str]]) -> str:
        """
        Generate a prompt for project-related queries with memory.
        """
        logger.debug(f"Generating query prompt for: {query}")
        context_str = "\n".join([f"Q: {item['query']}\nA: {item['response']}" for item in conversation_history])
        prompt = f"""
        You are an expert budget estimation assistant for freelancers. Respond ONLY with a JSON object containing EXACTLY three fields: 'response', 'follow_up_questions', and 'budget_estimation'. The 'response' must be 5-6 sentences long, providing a clear answer to the query. The 'follow_up_questions' must contain EXACTLY 4-5 relevant questions freelancers would ask clients. The 'budget_estimation' must provide a rough budget range based on assumptions or state 'More details needed' if vague. Use the conversation history for context and avoid repetition.

        Conversation History:
        {context_str}

        User Query: {query}

        Response Format:
        {{
          "response": "[Your response in 5-6 sentences]",
          "follow_up_questions": ["[Question 1]", "[Question 2]", "[Question 3]", "[Question 4]", "[Question 5, optional]"],
          "budget_estimation": "[Preliminary budget range or 'More details needed']"
        }}
        """
        logger.info("Query prompt generated")
        return prompt

    @staticmethod
    def get_general_prompt(query: str) -> str:
        """
        Generate a prompt for general queries.
        """
        logger.debug(f"Generating general prompt for: {query}")
        prompt = f"""
        You are a helpful assistant. Provide a concise and accurate response to the user's query in natural language. Do not include JSON or structured formats unless explicitly requested.

        Query: {query}
        """
        logger.info("General prompt generated")
        return prompt