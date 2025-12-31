import asyncio
import time
from langchain_mcp_adapters.client import MultiServerMCPClient

# Tickers to scan
TICKERS = [
    "AAPL", "MSFT", "GOOG", "AMZN", "TSLA", "META", "NVDA", "AMD", "INTC", "NFLX",
    "JPM", "BAC", "WFC", "GS", "MS", "C", "V", "MA", "AXP", "PYPL",
    "DIS", "CMCSA", "T", "VZ", "TMUS", "KO", "PEP", "MCD", "SBUX", "WMT"
]

# Client Config
MCP_SERVER_URL = "http://127.0.0.1:3000/mcp"

async def run_scanner():
    print(f"Connecting to MCP Server at {MCP_SERVER_URL}...")
    
    client = MultiServerMCPClient(
        {"mcp_server": {"transport": "streamable_http", "url": MCP_SERVER_URL}}
    )
    
    print("Connected. Fetching tools...")
    tools = await client.get_tools()
    get_option_data_tool = next((t for t in tools if t.name == "get_option_data"), None)
    
    if not get_option_data_tool:
        print("CRITICAL: 'get_option_data' tool not found!")
        return

    print(f"Starting HFT Scan of {len(TICKERS)} tickers...")
    print("Note: We expect drops (Backpressure) because the server queue size is 5.")
    
    start_time = time.perf_counter()
    
    # Create a list of async tasks (Firing them ALL at once)
    tasks = []
    for ticker in TICKERS:
        # We use ainvoke for concurrency
        task = get_option_data_tool.ainvoke({
            "ticker": ticker,
            "option_type": "call"
        })
        tasks.append(task)
        
    # GATHER: This runs them concurrently!
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.perf_counter()
    
    # Analyze Results
    success_count = 0
    drop_count = 0
    error_count = 0
    
    print("\n--- Scan Results ---")
    for i, res in enumerate(results):
        ticker = TICKERS[i]
        
        if isinstance(res, Exception):
            error_str = str(res)
            if "System Overloaded" in error_str:
                print(f"[{ticker}] DROPPED (Backpressure Active)")
                drop_count += 1
            else:
                print(f"[{ticker}] ERROR: {error_str}")
                error_count += 1
        else:
            # Success
            print(f"[{ticker}] SUCCESS")
            success_count += 1
            
    total_time = end_time - start_time
    print(f"\nSummary:")
    print(f"Total Time: {total_time:.4f}s")
    print(f"Total Requests: {len(TICKERS)}")
    print(f"SUCCESS: {success_count}")
    print(f"DROPPED: {drop_count}")
    print(f"ERRORS: {error_count}")
    
    if drop_count > 0:
        print("\n PASSED: Backpressure mechanism successfully rejected excess load.")
    else:
        print("\n WARNING: No drops. Server processed everything. Increase request count or decrease queue size?")

if __name__ == "__main__":
    try:
        asyncio.run(run_scanner())
    except KeyboardInterrupt:
        print("Scanner stopped.")
    except Exception as e:
        import traceback
        print(f"Fatal Error: {e}")
        traceback.print_exc()
