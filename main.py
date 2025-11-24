import asyncio
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import run_in_executor

# Ensure the correct package is installed: pip install langchain-mcp-adapters

llm = ChatOllama(model="granite4:3b", base_url="http://localhost:11434")

# Correct way to initialize the MCP Client for an HTTP server
# This configuration matches the expected format for MultiServerMCPClient
mcp_client = MultiServerMCPClient(
    {
        "mcp_server": {
            "transport": "streamable_http", # Use "streamable_http" for HTTP URLs
            "url": "http://127.0.0.1:3000/mcp" # Append /mcp if that's the endpoint
        }
    }
)

# The rest of the agent setup is done inside an async function or context
async def run_agent():
    # Use the client to get tools
    tools = await mcp_client.get_tools()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful options trading assistant. Use tools when needed."),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    result = await executor.ainvoke({"input": "Search the docs for MCP integration details and summarize."})
    print(result["output"])

# Run the asynchronous function
if __name__ == "__main__":
    # Use run_in_executor to invoke the async function synchronously
    # or just asyncio.run(run_agent()) if running in an async environment (like a Jupyter notebook)
    asyncio.run(run_agent())
