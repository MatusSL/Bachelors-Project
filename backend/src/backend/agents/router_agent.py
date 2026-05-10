import logging

from backend.schemas.constants import AppType
from backend.schemas.exceptions import AgentExecutionError


logger = logging.getLogger(__name__)


ROUTING_PROMPT = """
You are a routing classifier for a software requirements system.

Your task is to classify the user's project into ONE of the following categories:

WEB
MOBILE
API
DESKTOP
OTHER
UNKNOWN


Category definitions:

WEB
A browser-based application accessed via the internet.
Examples:
- SaaS platforms
- dashboards
- marketplaces
- blogs
- admin panels
- e-commerce websites


MOBILE
A mobile application designed for smartphones or tablets.
Examples:
- iOS apps
- Android apps
- Flutter / React Native apps
- apps installed from app stores


API
A backend service exposing programmatic endpoints.
Examples:
- REST APIs
- GraphQL services
- microservices
- backend services consumed by apps


DESKTOP
A native application running on a desktop operating system.
Examples:
- Windows applications
- macOS applications
- Linux applications
- Electron apps
- productivity tools installed on a computer


OTHER
Applications that do not fit WEB, MOBILE, API or DESKTOP categories but still have a clear purpose and architecture.
Examples:
- CLI / terminal tools
- AI agents or LLM-based systems
- automation scripts or workflows
- data pipelines / ETL systems
- background workers or job processors
- system integrations or orchestration tools
- video games
- mobile games
- PC / console games
- browser-based games
- game engines or game logic systems



UNKNOWN
Use this ONLY if:
- The project type cannot be determined
- OR the description is too vague or ambiguous


Rules:

- Return ONLY one word.
- Do NOT explain your reasoning.
- Do NOT include punctuation.
- Do NOT include additional text.

- Prefer WEB, MOBILE, API, or DESKTOP if there is a clear match.
- Use OTHER only when the project clearly does not fit WEB, MOBILE, API, DESKTOP, or GAMES.
- Use UNKNOWN only when there is insufficient information.


User message:
{user_input}
"""


class RouterService:
    def __init__(self, runner, router_agent) -> None:
        self.runner = runner
        self.router_agent = router_agent

    def detect_app_type(self, user_input: str) -> AppType:
        prompt = ROUTING_PROMPT.format(user_input=user_input)

        try:
            response = self.runner.invoke_agent(self.router_agent, prompt)

        except AgentExecutionError:
            logger.error(
                "Failed to detect app type due to agent execution error.",
            )
            raise
        
        app_type = response.strip().upper()

        mapping = {
            "WEB": AppType.WEB,
            "MOBILE": AppType.MOBILE,
            "API": AppType.API,
            "DESKTOP": AppType.DESKTOP,
            "OTHER": AppType.OTHER,
            "UNKNOWN": AppType.UNKNOWN,
        }

        return mapping.get(app_type, AppType.UNKNOWN)
