"""
Guardrail-related data models for the meta-agent package.

This module contains the GuardrailDefinition model that defines the structure
of a guardrail for an agent.
"""

from typing import Literal
from pydantic import BaseModel, Field


class GuardrailDefinition(BaseModel):
    """Definition of a guardrail for an agent.

    Pipeline role: produced by Step 4 (guardrail designer). Each definition
    describes one validation rule. The code generator (Step 7) turns this into
    an @input_guardrail or @output_guardrail decorated function.

    - "input"  guardrails run before the agent processes a user query.
    - "output" guardrails run after the agent produces its response.
    """

    name: str = Field(description="Name of the guardrail")
    # Literal type ensures only "input" or "output" are accepted by Pydantic.
    type: Literal["input", "output"] = Field(description="Type of guardrail (input or output)")
    validation_logic: str = Field(description="Logic for validating input or output")
    # implementation holds the finished @input_guardrail / @output_guardrail source code.
    implementation: str = Field(description="Python code implementing the guardrail")
