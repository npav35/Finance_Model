import asyncio
import sys
from unittest.mock import patch

# Mock input to avoid blocking
def mock_input(prompt):
    if "ticker" in prompt:
        return "AAPL"
    if "price" in prompt:
        return "150"
    if "date" in prompt:
        return "2025-01-01"
    return ""

async def run_benchmark():
    print("Starting benchmark...")
    # patching input in main module
    with patch('builtins.input', side_effect=mock_input):
        import main
        # We need to run the agent. main.run_agent is async.
        # However, main.py has `if __name__ == "__main__": asyncio.run(run_agent())`
        # We can import `run_agent` and run it.
        await main.run_agent()

if __name__ == "__main__":
    # Ensure current dir is in path
    sys.path.append(".")
    asyncio.run(run_benchmark())
