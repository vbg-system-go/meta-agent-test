"""
Core functionality for the meta-agent package.

This module implements the main generate_agent function that orchestrates
the agent generation process.

Pipeline overview (11 steps):
  Design phase  (steps 1-4): parse the spec, decide tools / output type / guardrails
  Code phase    (steps 5-9): generate Python code for every component
  Assembly      (step 10):   combine all code into a single deployable file set
  Validation    (step 11):   sanity-check the finished implementation
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

# ── Default fallback strings ──────────────────────────────────────────────────
# Used when the LLM assembler doesn't return its own versions.
# Stored as module-level constants so they're easy to update in one place.

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


# ── Helper functions ──────────────────────────────────────────────────────────

def _extract_json(result: Any, expected_type: type = dict, default: Any = None) -> Any:
    """Extract and parse JSON from a Runner result's final_output.

    Runner.run() returns a RunResult object whose .final_output is a raw JSON
    string. This helper centralises the parse-and-type-check logic so we don't
    repeat the same try/except block throughout the pipeline.
    """
    # When no explicit default is given, use an empty collection that matches
    # the caller's expected type (list for list steps, None for optional dicts).
    if default is None:
        default = [] if expected_type is list else None
    if hasattr(result, "final_output") and result.final_output:
        try:
            data = json.loads(result.final_output)
            # Only return the parsed value if it is the right Python type;
            # a type mismatch (e.g. LLM returned a dict when we expected a list)
            # is treated the same as a parse failure.
            if isinstance(data, expected_type):
                return data
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            logger.debug("Failed to parse JSON from result: %s", e)
    return default


def _extract_text(result: Any) -> str:
    """Extract plain text from a Runner result's final_output.

    Used for steps that produce raw Python source code rather than JSON
    (tool code, guardrail code, agent creation code, runner code).
    """
    if hasattr(result, "final_output") and result.final_output:
        return result.final_output
    return ""


# ── Main pipeline ─────────────────────────────────────────────────────────────

async def generate_agent(specification: str) -> AgentImplementation:
    """
    Generate an agent based on a natural language specification.

    Args:
        specification: Natural language description of the agent to create

    Returns:
        Complete agent implementation
    """
    # ── Pre-flight checks ─────────────────────────────────────────────────────
    # Validate early so we don't waste an API round-trip on empty input.
    if not specification or not specification.strip():
        raise ValueError("Agent specification cannot be empty")

    load_config()

    # Warn (but don't abort) if the API key is missing; the LLM call will fail
    # later with a clearer error from the SDK itself.
    if not check_api_key():
        print_api_key_warning()

    # ── Step 1: Parse the natural-language spec into structured data ──────────
    # The agent_generator LLM reads the raw specification and returns a JSON
    # object matching AgentSpecification. If parsing fails we fall back to
    # safe defaults so the pipeline can continue.
    logger.info("Step 1: Analyzing agent specification...")
    agent_spec_result = await Runner.run(
        agent_generator,
        f"Analyze this agent specification and extract structured information: {specification}",
    )
    logger.debug("Agent spec result: %s", agent_spec_result)

    agent_spec_dict = _extract_json(agent_spec_result, dict, {})
    # Fill in any fields the LLM omitted rather than letting Pydantic error out.
    agent_spec_dict.setdefault("name", "DefaultAgent")
    agent_spec_dict.setdefault("description", "Agent created from specification")
    agent_spec_dict.setdefault("instructions", specification)
    agent_specification = AgentSpecification(**agent_spec_dict)

    # ── Step 2: Decide which tools the agent will need ────────────────────────
    # Expected: a JSON array of tool descriptor objects.
    logger.info("Step 2: Designing agent tools...")
    tools_result = await Runner.run(
        agent_generator,
        f"Design tools for this agent: {agent_specification.model_dump_json()}",
    )
    logger.debug("Tools result: %s", tools_result)
    tools = _extract_json(tools_result, list, [])

    # ── Step 3: Optionally define a typed output schema ───────────────────────
    # Not all agents need structured output; None is a valid result here.
    logger.info("Step 3: Designing output type (if needed)...")
    output_type_result = await Runner.run(
        agent_generator,
        f"Design an output type for this agent if needed: {agent_specification.model_dump_json()}",
    )
    logger.debug("Output type result: %s", output_type_result)
    output_type_dict = _extract_json(output_type_result, dict, None)
    output_type = OutputTypeDefinition(**output_type_dict) if output_type_dict else None

    # ── Step 4: Decide which guardrails to enforce ────────────────────────────
    # Guardrails validate inputs before the agent runs and/or outputs after.
    logger.info("Step 4: Designing guardrails...")
    guardrails_result = await Runner.run(
        agent_generator,
        f"Design guardrails for this agent: {agent_specification.model_dump_json()}",
    )
    logger.debug("Guardrails result: %s", guardrails_result)
    guardrails = _extract_json(guardrails_result, list, [])

    # AgentDesign bundles spec + tools + output_type + guardrails into one
    # object that every subsequent generation step can reference.
    agent_design = AgentDesign(
        specification=agent_specification,
        tools=tools,
        output_type=output_type,
        guardrails=guardrails,
    )

    # ── Step 5: Generate Python code for each tool ────────────────────────────
    # One Runner.run() call per tool, so a spec with N tools makes N LLM calls.
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

    # ── Step 6: Generate the Pydantic output-type class (if applicable) ───────
    logger.info("Step 6: Generating output type code (if needed)...")
    output_type_code = None
    if agent_design.output_type:
        output_type_code_result = await Runner.run(
            agent_generator,
            f"Generate code for this output type: {agent_design.output_type.model_dump_json()}",
        )
        logger.debug("Output type code result: %s", output_type_code_result)
        # Use `or None` so an empty string collapses back to None.
        output_type_code = _extract_text(output_type_code_result) or None

    # ── Step 7: Generate Python code for each guardrail ───────────────────────
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

    # ── Step 8: Generate the Agent(...) constructor call ──────────────────────
    # This snippet instantiates the agent with its name, instructions, tools,
    # and guardrails wired in.
    logger.info("Step 8: Generating agent creation code...")
    agent_creation_result = await Runner.run(
        agent_generator,
        f"Generate code that creates an agent instance based on this design: {agent_design.model_dump_json()}",
    )
    logger.debug("Agent creation code result: %s", agent_creation_result)
    agent_creation_code = _extract_text(agent_creation_result)

    # ── Step 9: Generate the async runner / entry-point snippet ──────────────
    logger.info("Step 9: Generating runner code...")
    runner_code_result = await Runner.run(
        agent_generator,
        f"Generate code that runs the agent: {agent_design.model_dump_json()}",
    )
    logger.debug("Runner code result: %s", runner_code_result)
    runner_code = _extract_text(runner_code_result)

    # Collect all generated snippets into the intermediate AgentCode model.
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

    # ── Assemble all code sections into one main_code string ─────────────────
    # Sections are joined with double newlines to keep the output readable.
    # Each section is only included when it has content (guards against empty stubs).
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
    # run_agent() is the stable public API callers use to query the generated agent.
    sections.append(
        "# Function to run the agent from external code\n"
        "async def run_agent(query: str):\n"
        "    result = await Runner.run(agent, query)\n"
        "    return result"
    )
    agent_code.main_code = "\n\n".join(sections)

    # ── Step 10: Ask the LLM to finalize the full file layout ────────────────
    # The assembler may reorganize sections, add boilerplate, or split into
    # multiple files. If it returns a valid dict we use it; otherwise we fall
    # back to the code we assembled ourselves above.
    logger.info("Step 10: Assembling agent implementation...")
    implementation_result = await Runner.run(
        agent_generator,
        f"Assemble the complete agent implementation: {agent_code.model_dump_json()}",
    )
    logger.debug("Implementation result: %s", implementation_result)

    implementation_dict = _extract_json(implementation_result, dict, {})
    # Use setdefault so we never overwrite a value the LLM already provided.
    implementation_dict.setdefault("main_file", agent_code.main_code)
    implementation_dict.setdefault("installation_instructions", _DEFAULT_INSTALLATION)
    implementation_dict.setdefault("usage_examples", _DEFAULT_USAGE)
    implementation_dict.setdefault("additional_files", {})
    # Always include a requirements.txt unless the assembler already added one.
    implementation_dict["additional_files"].setdefault(
        "requirements.txt", _DEFAULT_REQUIREMENTS
    )

    agent_implementation = AgentImplementation(**implementation_dict)

    # ── Step 11: Validate the assembled implementation ────────────────────────
    # Currently a stub that always passes (see validation/validator.py).
    # Future: check syntax, verify imports, run a test query against the agent.
    logger.info("Step 11: Validating agent implementation...")
    validation_result = await Runner.run(
        agent_generator,
        f"Validate this agent implementation: {agent_implementation.model_dump_json()}",
    )
    if hasattr(validation_result, "final_output") and validation_result.final_output:
        logger.info("Validation message: %s", validation_result.final_output)

    return agent_implementation
