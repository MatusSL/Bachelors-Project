import logging

from backend.schemas.exceptions import AgentExecutionError
from backend.schemas.protocols import IntentDetectorProtocol


logger = logging.getLogger(__name__)


INTENT_PROMPT = """
You are an intent classifier for a software testing checklist assistant.

The assistant normally keeps asking the user questions until it has gathered all
project details, and only then generates the testing checklist.

Your task: decide whether the user's latest message is an explicit request to
generate / finish / produce the checklist RIGHT NOW, with the information gathered
so far — instead of answering more questions.

Answer YES only when the user clearly asks to generate, build, finish, or get the
checklist immediately. Messages may be in English or Slovak. Examples of YES:
- "just generate the checklist now"
- "that's enough, give me the checklist"
- "vygeneruj checklist teraz"
- "už staci, sprav mi ten zoznam"
- "skip the rest and produce it"

Answer NO for anything else, including normal answers to questions, general
discussion, or providing more project details.

Rules:
- Return ONLY one word: YES or NO.
- No explanation, no punctuation, no extra text.

User message:
{user_input}
"""


class IntentDetector(IntentDetectorProtocol):
    def __init__(self, runner, agent) -> None:
        self.runner = runner
        self.agent = agent

    def wants_checklist(self, user_input: str) -> bool:
        prompt = INTENT_PROMPT.format(user_input=user_input)

        try:
            response = self.runner.invoke_agent(self.agent, prompt)

        except AgentExecutionError:
            logger.error(
                "Failed to detect checklist intent due to agent execution error.",
            )
            raise

        return response.strip().upper().startswith("Y")
