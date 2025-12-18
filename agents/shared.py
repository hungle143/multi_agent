from langchain_openai import ChatOpenAI

# Single LLM instance shared across agents
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
