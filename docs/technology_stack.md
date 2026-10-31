# Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Chatbot UI | Streamlit + Python | User-facing loan application interface |
| Microservice | FastAPI + Python | REST API layer; validates and routes applications |
| Orchestration | LangGraph + LangChain | Multi-agent workflow coordination |
| Communication | FastMCP (HTTP-based) | MCP server framework for agent-to-data communication |
| Agent Implementation | FastAPI-based agents | Python functions invoked by the orchestrator |
| LLM | Anthropic Claude Sonnet 4.6 | Final loan decision classification |
| Agent SDK | Anthropic SDK | Claude API client |
| Prompt Engineering | Plain text template | Structured LLM prompting with schema constraint |
| Runtime | Python 3.12 | Application runtime |
