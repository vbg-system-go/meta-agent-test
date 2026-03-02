"""
Core functionality for the meta-agent package.

This module implements the main generate_agent function that orchestrates
the agent generation process.
"""

import json
import logging
from typing import Any

from agents import Runner

from meta_agent.models import (
    AgentSpecification,
    AgentDesign,
    AgentCode,
    AgentImplementation,
)
from meta_agent.generation.agent_generator import agent_generator
from meta_agent.config import load_config, check_api_key, print_api_key_warning
from meta_agent.models.output import OutputTypeDefinition

logger = logging.getLogger(__name__)

_DEFAULT_INSTALLATION = """\
# Installation Instructions

1. Create a virtual environment: `python -m venv venv`
2. Activate the virtual environment:
   - Windows: `venv\\Scripts\\activate`
   - macOS/Linux: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
"""

_DEFAULT_USAGE = """\
# Usage Examples

```python
import asyncio
from agent import run_agent

async def main():
    result = await run_agent("Your query here")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```
"""

_DEFAULT_REQUIREMENTS = "openai-agents>=0.0.6\npydantic>=2.0.0\npython-dotenv>=1.0.0\n"


def _extract_json(result: Any, expected_type: type = dict, default: Any = None) -> Any:
    """Extract and parse JSON from a Runner result's final_output."""
    if default is None:
        default = [] if expected_type is list else None
    if hasattr(result, "final_output") and result.final_output:
        try:
            data = json.loads(result.final_output)
            if isinstance(data, expected_type):
                return data
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.debug("Failed to parse JSON from result: %s", e)
    return default


def _extract_text(result: Any) -> str:
    """Extract plain text from a Runner result's final_output."""
    if hasattr(result, "final_output") and result.final_output:
        return result.final_output
    return ""


async def generate_agent(specification: str) -> AgentImplementation:
    """
    Generate an agent based on a natural language specification.

    Args:
        specification: Natural language description of the agent to create

    Returns:
        Complete agent implementation
    """
    if not specification or not specification.strip():
        raise ValueError("Agent specification cannot be empty")

    load_config()

    if not check_api_key():
        print_api_key_warning()

    # Step 1: Analyze the specification
    logger.info("Step 1: Analyzing agent specification...")
    agent_spec_result = await Runner.run(
        agent_generator,
        f"Analyze this agent specification and extract structured information: {specification}",
    )
    logger.debug("Agent spec result: %s", agent_spec_result)

    agent_spec_dict = _extract_json(agent_spec_result, dict, {})
    agent_spec_dict.setdefault("name", "DefaultAgent")
    agent_spec_dict.setdefault("description", "Agent created from specification")
    agent_spec_dict.setdefault("instructions", specification)
    agent_specification = AgentSpecification(**agent_spec_dict)

    # Step 2: Design the tools
    logger.info("Step 2: Designing agent tools...")
    tools_result = await Runner.run(
        agent_generator,
        f"Design tools for this agent: {agent_specification.model_dump_json()}",
    )
    logger.debug("Tools result: %s", tools_result)
    tools = _extract_json(tools_result, list, [])

    # Step 3: Design the output type
    logger.info("Step 3: Designing output type (if needed)...")
    output_type_result = await Runner.run(
        agent_generator,
        f"Design an output type for this agent if needed: {agent_specification.model_dump_json()}",
    )
    logger.debug("Output type result: %s", output_type_result)
    output_type_dict = _extract_json(output_type_result, dict, None)
    output_type = OutputTypeDefinition(**output_type_dict) if output_type_dict else None

    # Step 4: Design the guardrails
    logger.info("Step 4: Designing guardrails...")
    guardrails_result = await Runner.run(
        agent_generator,
        f"Design guardrails for this agent: {agent_specification.model_dump_json()}",
    )
    logger.debug("Guardrails result: %s", guardrails_result)
    guardrails = _extract_json(guardrails_result, list, [])

    agent_design = AgentDesign(
        specification=agent_specification,
        tools=tools,
        output_type=output_type,
        guardrails=guardrails,
    )

    # Step 5: Generate tool code
    logger.info("Step 5: Generating tool code...")
    tool_code_list = []
    for tool in agent_design.tools:
        tool_code = await Runner.run(
            agent_generator,
            f"Generate code for this tool: {tool}",
        )
        logger.debug("Tool code result: %s", tool_code)
        code = _extract_text(tool_code)
        if code:
            tool_code_list.append(code)

    # Step 6: Generate output type code
    logger.info("Step 6: Generating output type code (if needed)...")
    output_type_code = None
    if agent_design.output_type:
        output_type_code_result = await Runner.run(
            agent_generator,
            f"Generate code for this output type: {agent_design.output_type.model_dump_json()}",
        )
        logger.debug("Output type code result: %s", output_type_code_result)
        output_type_code = _extract_text(output_type_code_result) or None

    # Step 7: Generate guardrail code
    logger.info("Step 7: Generating guardrail code...")
    guardrail_code_list = []
    for guardrail in agent_design.guardrails:
        guardrail_code = await Runner.run(
            agent_generator,
            f"Generate code for this guardrail: {guardrail}",
        )
        logger.debug("Guardrail code result: %s", guardrail_code)
        code = _extract_text(guardrail_code)
        if code:
            guardrail_code_list.append(code)

    # Step 8: Generate agent creation code
    logger.info("Step 8: Generating agent creation code...")
    agent_creation_result = await Runner.run(
        agent_generator,
        f"Generate code that creates an agent instance based on this design: {agent_design.model_dump_json()}",
    )
    logger.debug("Agent creation code result: %s", agent_creation_result)
    agent_creation_code = _extract_text(agent_creation_result)

    # Step 9: Generate runner code
    logger.info("Step 9: Generating runner code...")
    runner_code_result = await Runner.run(
        agent_generator,
        f"Generate code that runs the agent: {agent_design.model_dump_json()}",
    )
    logger.debug("Runner code result: %s", runner_code_result)
    runner_code = _extract_text(runner_code_result)

    agent_code = AgentCode(
        imports=[
            "import os",
            "import asyncio",
            "from dotenv import load_dotenv",
            "from agents import Runner, function_tool, output_guardrail, GuardrailFunctionOutput",
            "from typing import Dict, List, Any, Optional",
            "from pydantic import BaseModel, Field",
        ],
        tool_implementations=tool_code_list,
        output_type_implementation=output_type_code,
        guardrail_implementations=guardrail_code_list,
        agent_creation=agent_creation_code,
        runner_code=runner_code,
    )

    # Assemble main code from components
    sections = ["\n".join(agent_code.imports)]
    if agent_code.tool_implementations:
        sections.append("# Tool implementations")
        sections.append("\n\n".join(agent_code.tool_implementations))
    if agent_code.output_type_implementation:
        sections.append("# Output type implementation")
        sections.append(agent_code.output_type_implementation)
    if agent_code.guardrail_implementations:
        sections.append("# Guardrail implementations")
        sections.append("\n\n".join(agent_code.guardrail_implementations))
    if agent_code.agent_creation:
        sections.append("# Agent creation")
        sections.append(agent_code.agent_creation)
    if agent_code.runner_code:
        sections.append("# Runner code")
        sections.append(agent_code.runner_code)
    sections.append(
        "# Function to run the agent from external code\n"
        "async def run_agent(query: str):\n"
        "    result = await Runner.run(agent, query)\n"
        "    return result"
    )
    agent_code.main_code = "\n\n".join(sections)

    # Step 10: Assemble the implementation
    logger.info("Step 10: Assembling agent implementation...")
    implementation_result = await Runner.run(
        agent_generator,
        f"Assemble the complete agent implementation: {agent_code.model_dump_json()}",
    )
    logger.debug("Implementation result: %s", implementation_result)

    implementation_dict = _extract_json(implementation_result, dict, {})
    implementation_dict.setdefault("main_file", agent_code.main_code)
    implementation_dict.setdefault("installation_instructions", _DEFAULT_INSTALLATION)
    implementation_dict.setdefault("usage_examples", _DEFAULT_USAGE)
    implementation_dict.setdefault("additional_files", {})
    implementation_dict["additional_files"].setdefault(
        "requirements.txt", _DEFAULT_REQUIREMENTS
    )

    agent_implementation = AgentImplementation(**implementation_dict)

    # Step 11: Validate the implementation
    logger.info("Step 11: Validating agent implementation...")
    validation_result = await Runner.run(
        agent_generator,
        f"Validate this agent implementation: {agent_implementation.model_dump_json()}",
    )
    if hasattr(validation_result, "final_output") and validation_result.final_output:
        logger.info("Validation message: %s", validation_result.final_output)

    return agent_implementation
