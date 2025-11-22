from ollama import chat
from ollama import ChatResponse
from langchain_community.chat_models import ChatOllama
from langchain_mcp import MCPToolkit
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOllama(model="qwen2.5-coder:14b", base_url="http://localhost:11434")
toolkit = MCPToolkit.from_uri("mcp://localhost:3000")
tools = toolkit.get_tools()

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant. Use tools when needed."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

agent = create_tool_calling_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

result = executor.invoke({"input": "Search the docs for MCP integration details and summarize."})
print(result["output"])