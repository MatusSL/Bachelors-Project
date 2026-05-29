import json
import logging
from typing import Dict, List

from backend.schemas.exceptions import AgentExecutionError
from langchain.agents import create_agent
from langchain.chat_models import BaseChatModel
from langchain_core.runnables import Runnable

from backend.agents.runner import Runner
from backend.schemas.constants import PriorityMap, Schema


logger = logging.getLogger(__name__)


CHECKLIST_PROMPT = """
You are a software testing expert. Generate a comprehensive testing checklist for the project described below.

--------------------------------------------------
PROJECT INFORMATION
--------------------------------------------------
{schema}

--------------------------------------------------
DOMAIN FOCUS
--------------------------------------------------
{domain_rules}

--------------------------------------------------
IDENTIFIED RISKS ({risk_count} total, sorted HIGH → MEDIUM → LOW)
--------------------------------------------------
{risks}

--------------------------------------------------
UNKNOWN / NOT PROVIDED FIELDS
--------------------------------------------------
{unknown_fields}

--------------------------------------------------
INSTRUCTIONS
--------------------------------------------------

1. Write a plain-text testing checklist based on the project information and identified risks.

2. Group test items under three sections: HIGH PRIORITY, MEDIUM PRIORITY, LOW PRIORITY.

3. You MUST write at least one test case for EVERY risk in the list above. Do not skip any.
   There are {risk_count} risks — your checklist must address all of them.

4. For each risk, write 1-3 concrete, actionable test cases.
   Use the actual project values (app name, auth types, roles, browsers, etc.) to make items specific.

5. Format exactly as:

[HIGH PRIORITY]
- <test case>
- <test case>

[MEDIUM PRIORITY]
- <test case>

[LOW PRIORITY]
- <test case>

6. Be specific and actionable. Never write vague items like "test the login" — write
   "Verify that login with an expired token returns a 401 and redirects to the login page."

7. Do not include risks that did not apply to this project.

8. The UNKNOWN / NOT PROVIDED FIELDS section lists project details the user did NOT
   provide. Do NOT invent concrete values for them. For areas they cover, write generic
   test cases and explicitly note the assumption (e.g. "Assuming token-based auth, ...").
   If that section says all details were provided, ignore this rule.

9. Return only the checklist. No preamble, explanation, or closing remarks.
"""


class ChecklistGenerator:
    def __init__(self, runner: Runner, model: BaseChatModel) -> None:
        self.runner = runner
        self.agent: Runnable = create_agent(model=model)

    def generate(
        self,
        schema: Schema,
        domain_rules: str,
        risk_rules: List[Dict],
        priority_map: PriorityMap,
        unknown_fields: List[str] | None = None,
    ) -> str:
        applicable = self._evaluate_risks(schema, risk_rules)
        sorted_risks = self._sort_risks(applicable, priority_map)

        serialized = [
            {
                "risk": r["risk"],
                "category": r["category"],
                "priority": r["priority"].name,
                "reason": r["reason"],
            }
            for r in sorted_risks
        ]

        prompt = CHECKLIST_PROMPT.format(
            schema=json.dumps(schema, indent=2),
            domain_rules=domain_rules,
            risks=json.dumps(serialized, indent=2),
            risk_count=len(serialized),
            unknown_fields=self._format_unknown_fields(unknown_fields),
        )
        try:
            return self.runner.invoke_agent(self.agent, prompt)
        except AgentExecutionError:
            logger.error(
                "Failed to generate checklist due to agent execution error.",
            )
            raise

    def _format_unknown_fields(self, unknown_fields: List[str] | None) -> str:
        if not unknown_fields:
            return "All project details were provided."

        listed = "\n".join(f"- {field}" for field in unknown_fields)
        return (
            "The user requested the checklist before providing these details:\n"
            f"{listed}"
        )

    def _evaluate_risks(self, schema: Schema, risk_rules: List[Dict]) -> List[Dict]:
        applicable = []
        for rule in risk_rules:
            if all(self._resolve_path(schema, cond) for cond in rule["conditions"]):
                applicable.append(rule)
        return applicable

    def _sort_risks(self, risks: List[Dict], priority_map: PriorityMap) -> List[Dict]:
        block_priority: Dict[str, int] = {}
        for priority, blocks in priority_map.items():
            for block in blocks:
                block_priority[block] = priority.value

        def sort_key(rule: Dict):
            block = rule["conditions"][0].split(".")[0]
            block_p = block_priority.get(block, rule["priority"].value)
            return (block_p, rule["priority"].value)

        return sorted(risks, key=sort_key)

    def _resolve_path(self, schema: Schema, path: str) -> bool:
        current = schema
        for key in path.split("."):
            if not isinstance(current, dict) or key not in current:
                return False
            current = current[key]
        return bool(current)
