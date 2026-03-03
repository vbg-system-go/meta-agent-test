"""
Agent creation code generator for the meta-agent package.

This module contains the main meta agent that orchestrates the whole agent generation process.
"""

from agents import Agent, function_tool

# ── Design-phase tools (steps 1-4) ───────────────────────────────────────────
# These @function_tool functions are exposed to the LLM so it can call them
# when it needs to analyse a spec or decide what to build.
from meta_agent.design.analyzer import analyze_agent_specification
from meta_agent.design.tool_designer import design_agent_tools
from meta_agent.design.output_designer import design_output_type
from meta_agent.design.guardrail_designer import design_guardrails

# ── Code-generation-phase tools (steps 5-10) ─────────────────────────────────
# These produce Python source code for each component of the generated agent.
from meta_agent.generation.tool_generator import generate_tool_code
from meta_agent.generation.output_generator import generate_output_type_code
from meta_agent.generation.guardrail_generator import generate_guardrail_code
from meta_agent.generation.runner_generator import generate_runner_code
from meta_agent.generation.assembler import assemble_agent_implementation

# ── Validation tool (step 11) ─────────────────────────────────────────────────
from meta_agent.validation.validator import validate_agent_implementation


@function_tool()
def generate_agent_creation_code() -> str:
    """
    Generate code that creates an agent instance based on the provided specification.

    Returns:
        Python code that creates the agent
    """
    # TODO: implement with actual LLM call
    # For now, emit a minimal Agent() constructor as a placeholder so that the
    # assembled file is at least syntactically valid.
    code_parts = []

    # Standard imports the generated file will need
    code_parts.append("from agents import Agent, ModelSettings")
    code_parts.append("from agents import function_tool")
    code_parts.append("from pydantic import BaseModel")

    # Placeholder agent definition; the real LLM call will substitute proper
    # name, instructions, tools, and guardrails here.
    code_parts.append("\n# Create the agent")
    code_parts.append("agent = Agent(")
    code_parts.append("    name=\"TestAgent\",")
    code_parts.append("    instructions=\"\"\"Test instructions\"\"\",")
    code_parts.append(")")

    return "\n".join(code_parts)


# ── The meta-agent that drives the entire generation pipeline ─────────────────
# agent_generator is an OpenAI Agents SDK Agent instance. core.py calls
# Runner.run(agent_generator, prompt) for each pipeline step. The LLM decides
# which of the registered tools to invoke and in what order.
#
# NOTE: openai-agents v0.0.6 does not accept `model` or `handoffs` kwargs.
agent_generator = Agent(
    name="agent_generator",
    instructions="""
    You are an agent generator designed to create other agents using the OpenAI Agents SDK.
    You take a natural language description of an agent design and produce Python code
    for a fully functional agent.

    Your workflow:
    1. Analyze the natural language specification
    2. Design tools, output types, and guardrails
    3. Generate code for each component
    4. Assemble the complete implementation
    5. Validate the implementation

    You will use specialized agents for each step of the process.
    """,
    # Each entry is a @function_tool-decorated callable; the SDK exposes them to
    # the LLM as callable functions with JSON-schema-described parameters.
    tools=[
        analyze_agent_specification,
        design_agent_tools,
        design_output_type,
        design_guardrails,
        generate_tool_code,
        generate_output_type_code,
        generate_guardrail_code,
        generate_agent_creation_code,
        generate_runner_code,
        assemble_agent_implementation,
        validate_agent_implementation,
    ],
)
