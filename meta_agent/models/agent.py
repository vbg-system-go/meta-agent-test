"""
Agent-related data models for the meta-agent package.

This module contains the AgentSpecification model that defines the structure
of an agent to be created.
"""

from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field


class AgentSpecification(BaseModel):
    """Input specification for an agent to be created."""
    name: str = Field(default="DefaultAgent", description="Name of the agent")
    description: str = Field(default="", description="Brief description of the agent's purpose")
    instructions: str = Field(default="", description="Detailed instructions for the agent")
    tools: List[Dict[str, Any]] = Field(default_factory=list, description="List of tools the agent needs")
    output_type: Optional[str] = None
    guardrails: List[Dict[str, Any]] = Field(default_factory=list, description="List of guardrails to implement")
    handoffs: List[Dict[str, Any]] = Field(default_factory=list, description="List of handoffs to other agents")
