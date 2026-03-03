"""
Implementation-related data models for the meta-agent package.

This module contains the AgentImplementation model that defines the complete
implementation of an agent with all files.
"""

from typing import Dict
from pydantic import BaseModel, Field


class AgentImplementation(BaseModel):
    """Complete agent implementation with all files.

    Pipeline role: the final deliverable returned by generate_agent(). The CLI
    writes each field to disk so the user ends up with a ready-to-run project.
    """

    # main_file → written to agent.py in the output directory
    main_file: str = Field(default="", description="Content of the main Python file")
    # additional_files maps filename → content, e.g. {"requirements.txt": "..."}
    additional_files: Dict[str, str] = Field(default_factory=dict, description="Additional files needed (filename: content)")
    # installation_instructions → written to INSTALL.md
    installation_instructions: str = Field(default="", description="Instructions for installing dependencies")
    # usage_examples → written to USAGE.md
    usage_examples: str = Field(default="", description="Examples of how to use the agent")
