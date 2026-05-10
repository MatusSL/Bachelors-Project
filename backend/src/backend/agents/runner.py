import logging
import time

from backend.schemas.exceptions import AgentExecutionError
from httpx import HTTPError
from ollama import ResponseError as OllamaResponseError

from langchain.messages import HumanMessage, AIMessage
from langchain_core.runnables import Runnable
from langchain_core.exceptions import LangChainException

from backend.schemas.constants import LLMResponse


logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3
_RETRY_DELAYS = [1, 2]


class Runner:
    def __init__(self) -> None:
        pass

    def invoke_agent(self, agent: Runnable, user_input: str) -> str:
        last_error: Exception | None = None

        for attempt in range(_MAX_ATTEMPTS):
            try:
                response: LLMResponse = agent.invoke(
                    {"messages": [HumanMessage(content=user_input)]}
                )

                try:
                    content = self._extract_content(response)
                    return content
                except ValueError as e:
                    raise AgentExecutionError() from e

            except OllamaResponseError as e:
                if e.status_code >= 500:
                    logger.warning(
                        "Ollama cloud returned %s on attempt %d/%d.",
                        e.status_code, attempt + 1, _MAX_ATTEMPTS,
                        exc_info=e,
                    )
                    last_error = e
                    if attempt < _MAX_ATTEMPTS - 1:
                        time.sleep(_RETRY_DELAYS[attempt])
                    continue
                logger.error("Ollama returned non-retryable error %s.", e.status_code, exc_info=e)
                raise AgentExecutionError() from e

            except HTTPError as e:
                logger.warning(
                    "HTTP error on attempt %d/%d.",
                    attempt + 1, _MAX_ATTEMPTS,
                    exc_info=e,
                )
                last_error = e
                if attempt < _MAX_ATTEMPTS - 1:
                    time.sleep(_RETRY_DELAYS[attempt])
                continue

            except LangChainException as e:
                logger.error("Failed to execute agent due to LangChain error.", exc_info=e)
                raise AgentExecutionError() from e

        logger.error("All %d attempts failed.", _MAX_ATTEMPTS, exc_info=last_error)
        raise AgentExecutionError() from last_error
        

    def _extract_content(self, response: LLMResponse) -> str:
        try:
            last_message = response["messages"][-1]
            if isinstance(last_message, HumanMessage):
                logger.error(
                    "Invalid LLM response: Last message is HumanMessage",
                )
                raise ValueError()

            ai_message: AIMessage = last_message

            content = ai_message.content
            if isinstance(content, list):
                return " ".join(str(c) for c in content)

            return content

        except (KeyError, IndexError) as e:
            logger.error(
                "Invalid LLM response: missing or malformed 'messages' in response",
            )
            raise ValueError() from e
