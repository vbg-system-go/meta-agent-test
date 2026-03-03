"""
String utilities for the meta-agent package.

This module provides functions for string manipulation.
"""

import re
from typing import List


def camel_to_snake(name: str) -> str:
    """
    Convert a camelCase or PascalCase string to snake_case.

    Args:
        name: String in camelCase or PascalCase

    Returns:
        String in snake_case
    """
    # Two-pass regex approach:
    # Pass 1: insert underscore between a lowercase/digit and an uppercase
    #         letter followed by more lowercase letters (e.g. "camelCase" → "camel_Case").
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # Pass 2: insert underscore between a lowercase/digit and an uppercase
    #         letter (handles consecutive caps like "XMLParser" → "XML_Parser").
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def snake_to_camel(name: str) -> str:
    """
    Convert a snake_case string to camelCase.

    Args:
        name: String in snake_case

    Returns:
        String in camelCase
    """
    components = name.split('_')
    # Keep the first component lowercase; capitalise the first letter of every
    # subsequent component (str.title() handles the rest unchanged).
    return components[0] + ''.join(x.title() for x in components[1:])


def snake_to_pascal(name: str) -> str:
    """
    Convert a snake_case string to PascalCase.

    Args:
        name: String in snake_case

    Returns:
        String in PascalCase
    """
    # Unlike camelCase, PascalCase capitalises every component including the first.
    return ''.join(x.title() for x in name.split('_'))


def format_docstring(text: str, indent: int = 0) -> str:
    """
    Format a docstring with proper indentation.

    Args:
        text: Docstring text
        indent: Number of spaces to indent

    Returns:
        Formatted docstring with opening/closing triple-quotes.
    """
    lines = text.strip().split('\n')
    indentation = ' ' * indent

    # Open the docstring on the same line as the first line of text.
    result = [f'{indentation}"""' + (lines[0] if lines else '')]

    if len(lines) > 1:
        # PEP 257: the opening line should end with a space when followed by
        # a blank separator line before the body text.
        if result[0][-1] != ' ':
            result[0] += ' '
        result.append('')  # blank separator line between summary and body

    # Re-indent every remaining line with the requested indentation.
    for line in lines[1:]:
        result.append(f'{indentation}{line}')

    # Closing triple-quotes on their own line, at the same indent level.
    result.append(f'{indentation}"""')

    return '\n'.join(result)
