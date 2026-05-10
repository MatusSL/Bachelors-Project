import json
import logging
from typing import Dict, List
from backend.schemas.exceptions import AgentExecutionError
from langchain.agents import create_agent
from langchain.chat_models import BaseChatModel

from backend.agents.runner import Runner
from backend.schemas.constants import ContextMessage, Schema


logger = logging.getLogger(__name__)


CONVERSATION_PROMPT = """
You are an AI software architect helping gather requirements for a software project.

Your goal is to collect information needed to complete a structured project schema.

You will receive:
1. The current schema state
2. The list of missing schema fields
3. The conversation history
4. The user's latest message

Your job is to ask the next question(s) that help fill the missing fields.

--------------------------------------------------
DOMAIN RULES
--------------------------------------------------
{domain_rules}

--------------------------------------------------
CURRENT SCHEMA STATE
--------------------------------------------------
{schema}

--------------------------------------------------
MISSING FIELDS
Each field contains a hint explaining what it means.
--------------------------------------------------
{missing_fields}

--------------------------------------------------
CONVERSATION HISTORY
--------------------------------------------------
{history}

--------------------------------------------------
LATEST USER MESSAGE
--------------------------------------------------
{user_input}

--------------------------------------------------
RULES
--------------------------------------------------

1. Ask questions that correspond ONLY to the fields listed under MISSING FIELDS above.
   Do NOT ask about any field that is not in that list, even if you can see it in the schema.

2. Ask **no more than TWO questions** in a single response.

3. Prefer asking **one question** if possible.

4. Before asking about any missing field, scan the CONVERSATION HISTORY above.
   If the user already answered that field at any point in the history, do NOT ask again.
   The field may still appear as "missing" due to a processing delay — ignore it and move on.

5. Never ask about fields that already have values in the schema.

6. Follow the logical order of the schema.
   Do not jump randomly between unrelated sections.

7. If the user asks for clarification or examples (e.g. "what does that mean?", "give me an example"),
   provide a helpful explanation with concrete examples. Do NOT repeat the question or bounce it back.
   For example, if the user asks "what are accessibility requirements?", explain:
   "Accessibility requirements ensure your app is usable by people with disabilities — for example,
   screen reader support, keyboard navigation, or sufficient color contrast."

8. Never challenge or correct the user's answers.
   Treat all answers as valid requirements.

9. Be concise and conversational.

10. If only one field remains missing, ask only that question.

11. Never ask the same question twice. If the CONVERSATION HISTORY shows you already asked about a topic and the user responded, move on to the next unanswered field.

--------------------------------------------------
RESPONSE FORMAT
--------------------------------------------------

Return only the assistant message.

Do NOT include:
- explanations about the schema
- JSON
- lists of fields
- internal reasoning

Just ask the next question(s) naturally.
"""


class ConversationalAgent:
    def __init__(self, runner: Runner, model: BaseChatModel) -> None:
        self.runner = runner
        self.agent = create_agent(model=model)

    def reply(
        self,
        domain_rules: str,
        schema: Schema,
        missing_questions: List[Dict],
        history: List[ContextMessage],
        user_input: str,
    ) -> str:

        history_text = "\n".join(f"{m.role}: {m.content}" for m in history[-16:])

        prompt = CONVERSATION_PROMPT.format(
            domain_rules=domain_rules,
            schema=schema,
            missing_fields=json.dumps(missing_questions, indent=2),
            history=history_text,
            user_input=user_input,
        )

        try:
            response = self.runner.invoke_agent(self.agent, prompt)
            return response

        except AgentExecutionError:
            logger.error(
                "Failed to generate agent reply due to agent execution error.",
            )
            raise
