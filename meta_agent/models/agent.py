"""
Agent-related data models for the meta-agent package.

This module contains the AgentSpecification model that defines the structure
of an agent to be created.
"""

from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field


class AgentSpecification(BaseModel):
    """Input specification for an agent to be created.

    Pipeline role: produced by Step 1 (analyzer). The LLM parses the raw
    natural-language spec and populates these fields, which are then passed
    to every subsequent design and generation step.
    """

    name: str = Field(default="DefaultAgent", description="Name of the agent")
    description: str = Field(default="", description="Brief description of the agent's purpose")
    # instructions becomes the system prompt of the generated agent.
    instructions: str = Field(default="", description="Detailed instructions for the agent")
    # tools / guardrails / handoffs are generic dicts at this stage; they are
    # refined into typed objects by the design-phase tools in steps 2-4.
    tools: List[Dict[str, Any]] = Field(default_factory=list, description="List of tools the agent needs")
    output_type: Optional[str] = None  # Free-text hint; resolved to OutputTypeDefinition in Step 3
    guardrails: List[Dict[str, Any]] = Field(default_factory=list, description="List of guardrails to implement")
    handoffs: List[Dict[str, Any]] = Field(default_factory=list, description="List of handoffs to other agents")
