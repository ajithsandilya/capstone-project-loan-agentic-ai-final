# MCP Integration Quick Reference

## What Changed

✓ **Before:** Agents used REST-style HTTP calls  
✓ **After:** Agents use proper FastMCP Client for MCP protocol communication

## How Agents Communicate Now

All agents use the same pattern:

```python
from mcp_client import call_mcp_tool_sync

result = call_mcp_tool_sync(
    "http://localhost:8001",  # MCP server URL
    "tool_name",               # Tool name
    param1=value1,             # Tool arguments
    param2=value2,
)
```

## Agent-to-MCP Mapping

| Agent | MCP Server | Port | Tool |
|-------|-----------|------|------|
| Applicant Profile | ApplicantDB | 8001 | `get_applicant_context` |
| Financial Risk | RiskRulesDB | 8002 | `get_risk_rules` |
| Loan Decision | DecisionSynthesis | 8003 | `synthesize_decision` |
| Compliance | NotificationSystem | 8004 | `send_notification` |

## Test Execution

```bash
# Unit tests (no servers needed)
pytest tests/ -v --ignore=tests/test_mcp_servers.py
# Result: 22 PASSED

# Integration tests (requires servers running)
pytest tests/test_mcp_servers.py -v
# Result: 8 PASSED (when servers are up)

# All tests
pytest tests/ -v
# Result: 30 PASSED (when servers are up)
```

## Starting Services

```bash
# Terminal 1: Applicant DB
uvicorn mcp_servers.applicant_db.server:app --port 8001

# Terminal 2: Risk Rules DB
uvicorn mcp_servers.risk_rules_db.server:app --port 8002

# Terminal 3: Decision Synthesis
uvicorn mcp_servers.decision_synthesis.server:app --port 8003

# Terminal 4: Notification System
uvicorn mcp_servers.notification_system.server:app --port 8004

# Terminal 5: FastAPI
uvicorn microservice.main:app --reload --port 8000

# Terminal 6: Streamlit
streamlit run app/streamlit_app.py
```

## Testing an Agent Directly

```python
from agents.applicant_profile_agent import run_applicant_profile_agent
from tests.conftest import make_application

# With MCP servers running:
app = make_application()
result = run_applicant_profile_agent(app)
print(result)
```

## Modified Files Summary

**New Files:**
- `mcp_client.py` — Shared MCP client utility

**Updated Agents (4):**
- `agents/applicant_profile_agent.py`
- `agents/financial_risk_analysis_agent.py`
- `agents/loan_decision_agent.py`
- `agents/compliance_action_orchestrator_agent.py`

**Updated MCP Servers (4):**
- `mcp_servers/applicant_db/server.py`
- `mcp_servers/risk_rules_db/server.py`
- `mcp_servers/decision_synthesis/server.py`
- `mcp_servers/notification_system/server.py`

**Updated Tests (3):**
- `tests/conftest.py`
- `tests/test_agents.py`
- `tests/test_mcp_servers.py`

## Key Implementation Details

1. **MCP Client**: Uses official `FastMCP.Client` for HTTP transport
2. **Protocol**: JSON-RPC 2.0 over HTTP
3. **Endpoint**: Each server exposes `/mcp` endpoint
4. **Test Mode**: Automatic mocking via `set_mcp_post_override()` fixture
5. **Async**: Internal async calls wrapped for LangGraph sync compatibility
6. **Result Format**: Extracts `result.data` from `CallToolResult`

## No Changes Needed For

✓ Business logic (all rules preserved)  
✓ Pydantic models (API contracts unchanged)  
✓ LangGraph orchestration (same flow)  
✓ Claude Sonnet integration (same prompts)  
✓ Microservice endpoints (same API)  
✓ Streamlit UI (same interface)  

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection refused" | Start MCP servers first |
| "Task group not initialized" | Use `mcp.http_app()` to get FastAPI app |
| Tests fail with 404 | Tests need mocking fixture or running servers |
| Import error for FastMCP | Run `pip install -r requirements.txt` |

## Next Steps

1. Run unit tests: `pytest tests/ -v --ignore=tests/test_mcp_servers.py`
2. Start all MCP servers (6 terminals)
3. Run integration tests: `pytest tests/test_mcp_servers.py -v`
4. Start FastAPI: `uvicorn microservice.main:app --reload --port 8000`
5. Test via curl or Streamlit

## Documentation

Full details in: [MCP_AUDIT_REPORT.md](MCP_AUDIT_REPORT.md)
