import asyncio
import time
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from utils import perf_utils
# LLM: Ollama local model
llm = ChatOllama(model="granite4:3b", base_url="http://localhost:11434")

# MCP client config – assumes a streamable HTTP MCP server at port 3000
mcp_client = MultiServerMCPClient(
    {
        "mcp_server": {
            "transport": "streamable_http",
            "url": "http://127.0.0.1:3000/mcp",
        }
    }
)

async def run_agent():
    
    # Load MCP tools from the server
    tools = await mcp_client.get_tools()
    print("Loaded MCP tools:", [t.name for t in tools])

    # Wrap tools with performance timer
    for t in tools:
        if hasattr(t, 'coroutine') and t.coroutine:
            t.coroutine = perf_utils.time_it(f"Tool: {t.name}")(t.coroutine)
        if hasattr(t, 'func') and t.func:
             t.func = perf_utils.time_it(f"Tool: {t.name}")(t.func)

    if not tools:
        print("No tools loaded from MCP server. The agent will behave like a plain LLM.")
        print("   -> Check that your MCP server is running on http://127.0.0.1:3000/mcp")

    
    # Prompt: clarify MCP meaning so the model doesn't hallucinate "Managed Cloud Platform"
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful options trading assistant. "
                "Use Model Context Protocol exposed by the MCP server tools. "
                "Strictly follow this workflow:\n"
                "1. Use `get_option_data` to fetch the option details.\n"
                "2. IMMEDIATELY use the output from step 1 (S, K, T, r, sigma) to call the Greek calculation tools: "
                "`calculate_delta`, `calculate_gamma`, `calculate_theta`, `calculate_vega`, and `calculate_rho`.\n"
                "3. Analyze these Greeks to determine if the option is a good trade."
            ),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, return_intermediate_steps=True)

    # Ask it to actually use tools
    mode = input("Mode (single/batch): ").strip().lower() or "single"
    if mode not in {"single", "batch"}:
        print("Invalid mode. Use 'single' or 'batch'.")
        return

    ticker = input("Enter stock ticker: ") if mode == "single" else ""
    price = input("Enter target strike (or Enter for ATM): ") if mode == "single" else ""
    expiration_date = input("Enter expiration date (MM-DD-YYYY, or Enter for nearest): ") if mode == "single" else ""
    option_type = input("Enter option type (call/put): ")
    batch_tickers = input("Batch scan tickers (comma-separated; uses nearest expiration + ATM strike per ticker): ") if mode == "batch" else ""

    # Construct prompt parts dynamically to handle optional inputs
    strike_part = f"strike {price}" if price.strip() else "ATM strike"
    date_part = f"expiration {expiration_date}" if expiration_date.strip() else "nearest expiration"

    if mode == "batch":
        # Fire concurrent requests to exercise backpressure without multiple clients.
        tickers = [t.strip().upper() for t in batch_tickers.split(",") if t.strip()]
        get_option_data_tool = next((t for t in tools if t.name == "get_option_data"), None)
        if not get_option_data_tool:
            print("CRITICAL: 'get_option_data' tool not found!")
            return
        print(f"Starting batch scan of {len(tickers)} tickers...")
        start_time = time.perf_counter()
        tasks = [
            get_option_data_tool.ainvoke({
                "ticker": t,
                "option_type": option_type,
                "expiration_date": None,
                "strike": None
            })
            for t in tickers
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.perf_counter()
        success_count = 0
        drop_count = 0
        error_count = 0
        print("\n--- Batch Results ---")
        for i, res in enumerate(results):
            t = tickers[i]
            if isinstance(res, Exception):
                error_str = str(res)
                if "System Overloaded" in error_str:
                    print(f"[{t}] DROPPED (Backpressure Active)")
                    drop_count += 1
                else:
                    print(f"[{t}] ERROR: {error_str}")
                    error_count += 1
            else:
                print(f"[{t}] SUCCESS")
                success_count += 1
        total_time = end_time - start_time
        print(f"\nSummary:")
        print(f"Total Time: {total_time:.4f}s")
        print(f"Total Requests: {len(tickers)}")
        print(f"SUCCESS: {success_count}")
        print(f"DROPPED: {drop_count}")
        print(f"ERRORS: {error_count}")
        return

    with perf_utils.Timer("Total Agent Execution"):
        result = await executor.ainvoke({
            "input": (
                f"Use MCP tools to get {ticker} {option_type} data for {strike_part} and {date_part} "
                "and summarize it, telling me if it is a good trade."
            )
        })
    
    print("\n=== TOOLS USED ===")
    for step in result["intermediate_steps"]:
        action = step[0]
        print(f"Tool: {action.tool}, Input: {action.tool_input}")

    print("\n=== FINAL OUTPUT ===")
    print(result["output"])



if __name__ == "__main__":
    asyncio.run(run_agent())
