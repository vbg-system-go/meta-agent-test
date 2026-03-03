"""
Output-related data models for the meta-agent package.

This module contains the OutputTypeDefinition model that defines the structure
of an output type for an agent.
"""

from typing import Any, List, Dict
from pydantic import BaseModel, Field


class OutputTypeDefinition(BaseModel):
    """Definition of a structured output type.

    Pipeline role: produced by Step 3 (output designer) when the agent needs
    to return structured data rather than free-form text. The code generator
    (Step 6) emits a Pydantic BaseModel subclass from this definition.
    The OpenAI Agents SDK uses the model's JSON schema to validate agent output.
    """

    name: str = Field(description="Name of the output type")
    # Each field dict has keys: name, type, description (and optionally default).
    fields: List[Dict[str, Any]] = Field(description="Fields in the output type")
    # code holds the finished Pydantic model source that will be included in agent.py.
    code: str = Field(description="Python code defining the output type")
