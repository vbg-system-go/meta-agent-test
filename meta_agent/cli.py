"""
Command Line Interface for Meta Agent

This module provides a command-line interface for the Meta Agent.
"""

import asyncio
import argparse
import sys
import os

from meta_agent.core import generate_agent
from meta_agent.config import config, load_config, check_api_key, print_api_key_warning
from meta_agent.utils import write_file


def main():
    """Main entry point for the CLI."""
    # Load .env and populate the global Config singleton before anything else.
    load_config()

    # Fail fast with a clear message if no API key is available; the generation
    # pipeline would fail anyway but with a less helpful error from the SDK.
    if not check_api_key():
        print_api_key_warning()
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Meta Agent - Generate OpenAI Agents SDK agents from natural language specifications"
    )
    # The spec can be supplied inline (--spec) or via a file (--file).
    # Exactly one of the two must be provided.
    parser.add_argument(
        "--spec", "-s",
        type=str,
        help="Natural language specification for the agent to generate"
    )
    parser.add_argument(
        "--file", "-f",
        type=str,
        help="Path to a file containing the agent specification"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=".",
        help="Output directory for the generated agent code (default: current directory)"
    )

    args = parser.parse_args()

    # ── Resolve the specification text ────────────────────────────────────────
    specification = ""
    if args.file:
        # Read spec from a file (useful for long or multi-line specs).
        try:
            with open(args.file, "r") as f:
                specification = f.read()
        except Exception as e:
            print(f"Error reading specification file: {e}")
            sys.exit(1)
    elif args.spec:
        specification = args.spec
    else:
        # Neither flag was given; print usage and exit.
        parser.print_help()
        sys.exit(1)

    def write_and_report(path: str, content: str) -> None:
        """Write a file to disk and print a confirmation line."""
        write_file(path, content)
        print(f"Generated: {path}")

    # ── Run the generation pipeline ───────────────────────────────────────────
    # asyncio.run() starts a fresh event loop for the async generate_agent call.
    try:
        agent_implementation = asyncio.run(generate_agent(specification))

        # Create the output directory if it doesn't already exist.
        os.makedirs(args.output, exist_ok=True)

        # Write all output files.
        write_and_report(os.path.join(args.output, "agent.py"), agent_implementation.main_file)

        # additional_files contains supporting files such as requirements.txt.
        for filename, content in agent_implementation.additional_files.items():
            write_and_report(os.path.join(args.output, filename), content)

        if agent_implementation.installation_instructions:
            write_and_report(os.path.join(args.output, "INSTALL.md"), agent_implementation.installation_instructions)

        if agent_implementation.usage_examples:
            write_and_report(os.path.join(args.output, "USAGE.md"), agent_implementation.usage_examples)

        # Also print the instructions to stdout for quick reference.
        print("\nInstallation Instructions:")
        print(agent_implementation.installation_instructions)
        print("\nUsage Examples:")
        print(agent_implementation.usage_examples)

    except Exception as e:
        print(f"Error generating agent: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
