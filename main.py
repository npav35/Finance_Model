import asyncio
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

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
    # 🔹 Load MCP tools from the server
    tools = await mcp_client.get_tools()
    print("Loaded MCP tools:", [t.name for t in tools])

    if not tools:
        print("No tools loaded from MCP server. The agent will behave like a plain LLM.")
        print("   -> Check that your MCP server is running on http://127.0.0.1:3000/mcp")
    
    # Prompt: clarify MCP meaning so the model doesn't hallucinate "Managed Cloud Platform"
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant. "
                "When I say MCP, I mean the **Model Context Protocol** tools "
                "exposed by the connected MCP server,. "
                "Use tools when they are helpful."
            ),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # Ask it to actually use tools
    result = await executor.ainvoke({
    "input": "Use MCP tools to get AAPL 320 call data for expiration 2025-12-19 and summarize it."
})
    print("\n=== FINAL OUTPUT ===")
    print(result["output"])

if __name__ == "__main__":
    asyncio.run(run_agent())