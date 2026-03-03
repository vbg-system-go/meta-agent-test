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
    """Complete design for an agent.

    Pipeline role: assembled after Steps 1-4. Bundles the parsed specification
    with the fully typed tool, output, and guardrail definitions so that every
    code-generation step (5-9) has the full picture in one object.
    """

    specification: AgentSpecification = Field(description="Basic agent specification")
    # ToolDefinition objects have typed parameters, unlike the raw dicts in AgentSpecification.
    tools: List[ToolDefinition] = Field(default_factory=list, description="Detailed tool definitions")
    output_type: Optional[OutputTypeDefinition] = None  # None means the agent returns plain text
    guardrails: List[GuardrailDefinition] = Field(default_factory=list, description="Detailed guardrail definitions")
