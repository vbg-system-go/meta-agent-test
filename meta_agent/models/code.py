"""
Code-related data models for the meta-agent package.

This module contains the AgentCode model that defines the structure of
generated agent code and related files.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class AgentCode(BaseModel):
    """Intermediate container for all generated Python code snippets.

    Pipeline role: populated during Steps 5-9. Each field holds the output of
    one generation step. core.py then concatenates these sections into main_code
    before passing the whole object to the assembler (Step 10).
    """

    # main_code starts empty; core.py writes to it after assembling all sections.
    main_code: str = Field(default="", description="Main Python code implementing the agent")
    imports: List[str] = Field(default_factory=list, description="Required imports")
    tool_implementations: List[str] = Field(default_factory=list, description="Code for tool implementations")
    output_type_implementation: Optional[str] = None  # None when no structured output is needed
    guardrail_implementations: List[str] = Field(default_factory=list, description="Code for guardrail implementations")
    # agent_creation holds the Agent(...) constructor call
    agent_creation: str = Field(default="", description="Code that creates the agent instance")
    # runner_code holds the async main() entry point
    runner_code: str = Field(default="", description="Code that runs the agent")
