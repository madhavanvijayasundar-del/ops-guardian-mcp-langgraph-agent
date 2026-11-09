from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from src.state import IncidentState
from src.tools import (
    mcp_read_pod_logs,
    mcp_read_terraform_runbook,
    mcp_execute_kubectl_remediation
)

def diagnose_incident_node(state: IncidentState) -> dict:
    service = state["service_name"]
    logs = mcp_read_pod_logs(service)
    
    if "OOMKilled" in logs:
        root_cause = "Container OOMKilled due to memory saturation under high throughput."
        runbook = mcp_read_terraform_runbook("OOMKilled")
        remediation_cmd = f"kubectl set resources deployment/{service} --limits=memory=1024Mi && kubectl rollout restart deployment/{service}"
        destructive = True
    else:
        root_cause = "Transient network timeout."
        remediation_cmd = f"kubectl rollout restart deployment/{service}"
        destructive = False
        
    audit = list(state.get("audit_trail", []))
    audit.append(f"[DIAGNOSIS COMPLETE] {root_cause}")
    
    return {
        "diagnosed_root_cause": root_cause,
        "proposed_remediation": remediation_cmd,
        "is_destructive_action": destructive,
        "execution_status": "AWAITING_APPROVAL",
        "audit_trail": audit
    }

def execute_remediation_node(state: IncidentState) -> dict:
    audit = list(state.get("audit_trail", []))
    
    if not state.get("human_approved", False):
        audit.append("[SECURITY ALERT] Action execution blocked: Operator approval missing.")
        return {
            "execution_status": "REJECTED_BY_OPERATOR",
            "audit_trail": audit
        }
        
    result = mcp_execute_kubectl_remediation(
        state["service_name"],
        state["proposed_remediation"]
    )
    audit.append(f"[EXECUTION SUCCESS] {result['message']}")
    
    return {
        "execution_status": "EXECUTED",
        "audit_trail": audit
    }

builder = StateGraph(IncidentState)
builder.add_node("diagnose_incident", diagnose_incident_node)
builder.add_node("execute_remediation", execute_remediation_node)

builder.add_edge(START, "diagnose_incident")
builder.add_edge("diagnose_incident", "execute_remediation")
builder.add_edge("execute_remediation", END)

checkpointer = MemorySaver()
app_graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=["execute_remediation"]
)
