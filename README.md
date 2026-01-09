# Finance Model Agent

An options trading assistant built with LangChain, Ollama, and MCP Tools.

## Description

This agent is designed to help with options trading analysis. It leverages a local LLM (via Ollama) and connects to an MCP server to retrieve real-time or historical options data. The agent can use tools provided by the MCP server to analyze trades and answer user queries.

## Prerequisites

- **Python 3.10+**
- **Ollama**: Running a model like `granite4:3b`. Make sure you use a model that supports tool calling.
  - Ensure Ollama is running on `http://localhost:11434`.
- **MCP Server**: A local MCP server running on port 3000.
  - The agent expects the server to be available at `http://127.0.0.1:3000/mcp`.

## Installation

1.  Clone the repository.
2.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Ensure your specific MCP server is running on port 3000.
2.  Run the agent:
    ```bash
    python main.py
    ```

### High-Load Stress Test
To verify the **Backpressure Pipeline**, run the stress test script:
```bash
python tests/stress_test.py
```
This utility simulates a burst of 30 concurrent market scans. The system successfully handles the first 5 requests (the queue depth) and then gracefully drops the remainder with a `System Overloaded` message, proving the stability of the backend architecture.

### Why Stress Testing? (Real-World Use Case)

This setup simulates a high-reliability trading platform. Consider a scenario with **7 users or portfolios** requesting data at the exact same millisecond, and the server queue size is 5:

1.  **Requests 1-6**: The server accepts the first request and puts the next 5 into an async queue. These users get fast, reliable results as soon as the worker is free.
2.  **Request 7**: Instead of trying to "do everything at once" (which causes slow-downs or system-wide crashes), the server immediately rejects the 7th request with a `System Overloaded` error.

This **Load Shedding** ensures that the system provides **deterministic performance**—it guarantees quality of service for existing users rather than failing for everyone.

## Architecture Diagram

```mermaid
graph LR
    subgraph Client ["Finance_Model Application"]
        A["LLM Trading Agent"]
        B["Stress test utility"]
    end

    subgraph Server ["mcp_calc Greeks Engine"]
        C["Async Backpressure Pipeline"]
        D["Black-Scholes Calculator"]
    end

    A -- "MCP Tools" --> C
    B -- "Concurrent Bursts" --> C
    C --> D
```

## Demo

![Agent Output Demo](demo_screenshot.png)