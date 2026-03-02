"""
Implementation-related data models for the meta-agent package.

This module contains the AgentImplementation model that defines the complete
implementation of an agent with all files.
"""

from typing import Dict
from pydantic import BaseModel, Field


class AgentImplementation(BaseModel):
    """Complete agent implementation with all files."""
    main_file: str = Field(default="", description="Content of the main Python file")
    additional_files: Dict[str, str] = Field(default_factory=dict, description="Additional files needed (filename: content)")
    installation_instructions: str = Field(default="", description="Instructions for installing dependencies")
    usage_examples: str = Field(default="", description="Examples of how to use the agent")
