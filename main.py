import asyncio
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
                "Use Model Context Protocol exposed by the MCP server tools when they are helpful"
                "First try to use the get_option_data tool to get the option data"
                "Then leverage the remaining tools if helpful to determine if the option is a good trade"
            ),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, return_intermediate_steps=True)

    # Ask it to actually use tools
    ticker = input("Enter stock ticker: ")
    price = input("Enter price: ")
    expiration_date = input("Enter expiration date (MM-DD-YYYY): ")
    option_type = input("Enter option type (call/put): ")

    with perf_utils.Timer("Total Agent Execution"):
        result = await executor.ainvoke({
            "input": (
                f"Use MCP tools to get {ticker} {price} {option_type} data for expiration {expiration_date} "
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