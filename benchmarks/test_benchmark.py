import asyncio
import sys
import os
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main
from utils import perf_utils

# Mock input to avoid blocking
def mock_input(prompt):
    if "ticker" in prompt:
        return "AAPL"
    if "strike" in prompt:
        return "150"
    if "date" in prompt:
        return "2026-01-16"
    if "option type" in prompt:
        return "call"
    return ""

async def run_benchmark():
    print("Starting benchmark...")
    # patching input in main module
    with patch('builtins.input', side_effect=mock_input):
        await main.run_agent()
        
        perf_utils.BenchmarkTracker().report()

if __name__ == "__main__":
    asyncio.run(run_benchmark())
