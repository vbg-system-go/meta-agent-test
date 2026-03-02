"""
Design-related data models for the meta-agent package.

This module contains the AgentDesign model that defines the complete design
for an agent, including its specification, tools, output type, and guardrails.
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from meta_agent.models.agent import AgentSpecification
from meta_agent.models.tool import ToolDefinition
from meta_agent.models.output import OutputTypeDefinition
from meta_agent.models.guardrail import GuardrailDefinition


class AgentDesign(BaseModel):
    """Complete design for an agent."""
    specification: AgentSpecification = Field(description="Basic agent specification")
    tools: List[ToolDefinition] = Field(default_factory=list, description="Detailed tool definitions")
    output_type: Optional[OutputTypeDefinition] = None
    guardrails: List[GuardrailDefinition] = Field(default_factory=list, description="Detailed guardrail definitions")
