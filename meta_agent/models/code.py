"""
Code-related data models for the meta-agent package.

This module contains the AgentCode model that defines the structure of
generated agent code and related files.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class AgentCode(BaseModel):
    """Generated agent code and related files."""
    main_code: str = Field(default="", description="Main Python code implementing the agent")
    imports: List[str] = Field(default_factory=list, description="Required imports")
    tool_implementations: List[str] = Field(default_factory=list, description="Code for tool implementations")
    output_type_implementation: Optional[str] = None
    guardrail_implementations: List[str] = Field(default_factory=list, description="Code for guardrail implementations")
    agent_creation: str = Field(default="", description="Code that creates the agent instance")
    runner_code: str = Field(default="", description="Code that runs the agent")
