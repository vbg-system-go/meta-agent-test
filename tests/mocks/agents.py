"""
Mock implementation of the OpenAI Agents SDK for testing.
"""
import json


class MockRunResult:
    """Mock RunResult returned by Runner.run()."""

    def __init__(self, data):
        if isinstance(data, (dict, list)):
            self.final_output = json.dumps(data)
        else:
            self.final_output = str(data)


class Agent:
    """Mock Agent class for testing."""

    def __init__(self, name=None, instructions=None, tools=None):
        self.name = name
        self.instructions = instructions
        self.tools = tools or []

    def tool(self, func=None):
        """Mock tool decorator."""
        def decorator(f):
            self.tools.append(f)
            return f

        if func is None:
            return decorator
        return decorator(func)


class Runner:
    """Mock Runner class for testing."""

    def __init__(self):
        pass

    @staticmethod
    async def run(agent, specification):
        """Mock run method that returns different results based on the specification."""
        if not specification or not specification.strip():
            raise ValueError("Agent specification cannot be empty")

        if "Analyze this agent specification" in specification:
            return MockRunResult({
                "name": "TestAgent",
                "description": "Test description",
                "instructions": "Test instructions"
            })
        elif "Design tools for this agent" in specification:
            return MockRunResult([{
                "name": "test_tool",
                "description": "A test tool",
                "parameters": [{"name": "param1", "type": "string", "required": True}],
                "return_type": "string",
                "implementation": "def test_tool(param1):\n    return f'Result: {param1}'"
            }])
        elif "Design an output type" in specification:
            return MockRunResult({
                "name": "TestOutput",
                "fields": [{"name": "result", "type": "string", "description": "Result of the tool execution"}],
                "code": "class TestOutput(BaseModel):\n    result: str = Field(description='Result of the tool execution')"
            })
        elif "Design guardrails" in specification:
            return MockRunResult([{
                "name": "test_guardrail",
                "description": "A test guardrail",
                "type": "input",
                "validation_logic": "Check if input contains sensitive information",
                "implementation": "def validate_input(input_text):\n    return 'password' not in input_text.lower()"
            }])
        elif "Generate code for this tool" in specification:
            return MockRunResult("def test_tool(param1):\n    return f'Result: {param1}'")
        elif "Generate code for this output type" in specification:
            return MockRunResult("class TestOutput(BaseModel):\n    result: str = Field(description='Result of the tool execution')")
        elif "Generate code for this guardrail" in specification:
            return MockRunResult("def validate_input(input_text):\n    return 'password' not in input_text.lower()")
        elif "Generate code that creates an agent instance" in specification:
            return MockRunResult("from agents import Agent\n\nagent = Agent(name='TestAgent', instructions='Test instructions')")
        elif "Generate code that runs the agent" in specification:
            return MockRunResult("from agents import Runner\n\n# Run the agent\nawait Runner.run(agent, user_input)")
        elif "Assemble the complete agent implementation" in specification:
            return MockRunResult({
                "main_file": (
                    "# Agent implementation for TestAgent\n"
                    "from agents import Agent, Runner\n\n"
                    "def test_tool(param1):\n    return f'Result: {param1}'\n\n"
                    "# Create the agent\n"
                    "agent = Agent(name='TestAgent', instructions='Test instructions')\n\n"
                    "async def main():\n    await Runner.run(agent, user_input)\n"
                ),
                "additional_files": {
                    "requirements.txt": "agents>=0.0.6\npython-dotenv>=1.0.0"
                },
                "installation_instructions": "pip install -r requirements.txt",
                "usage_examples": "python main.py"
            })
        elif "Validate this agent implementation" in specification:
            return MockRunResult({"valid": True, "message": "Agent implementation is valid"})
        return MockRunResult("Mock response for: " + specification[:50] + "...")


def function_tool(func=None, *, name=None, description=None):
    """Mock function_tool decorator."""
    def decorator(f):
        f._function_tool = True
        f._name = name or f.__name__
        f._description = description or f.__doc__
        return f

    if func is None:
        return decorator
    return decorator(func)
