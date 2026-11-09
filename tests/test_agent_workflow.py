import pytest
from src.agent import app_graph
from src.tools import MOCK_K8S_ENVIRONMENT

def test_human_in_the_loop_approval_flow():
    thread_config = {"configurable": {"thread_id": "incident_ticket_101"}}
    
    initial_input = {
        "incident_id": "INC-101",
        "service_name": "payment-service",
        "raw_error_log": "OOMKilled on node aks-pool-1",
        "diagnosed_root_cause": None,
        "proposed_remediation": None,
        "is_destructive_action": False,
        "human_approved": False,
        "execution_status": "PENDING_DIAGNOSIS",
        "audit_trail": []
    }
    
    # 1. Run until the interrupt boundary pauses execution
    app_graph.invoke(initial_input, config=thread_config)
    
    # 2. Verify state paused before execution
    paused_state = app_graph.get_state(thread_config)
    assert paused_state.next == ("execute_remediation",), "Agent failed to pause at interrupt boundary!"
    assert paused_state.values["execution_status"] == "AWAITING_APPROVAL"
    assert "kubectl set resources" in paused_state.values["proposed_remediation"]
    
    # 3. Simulate human approval and resume graph
    app_graph.update_state(thread_config, {"human_approved": True})
    final_state = app_graph.invoke(None, config=thread_config)
    
    # 4. Verify successful execution and healthy cluster
    assert final_state["execution_status"] == "EXECUTED"
    assert MOCK_K8S_ENVIRONMENT["payment-service"]["status"] == "Running"

def test_operator_rejection_blocks_execution():
    thread_config = {"configurable": {"thread_id": "incident_ticket_102"}}
    
    initial_input = {
        "incident_id": "INC-102",
        "service_name": "payment-service",
        "raw_error_log": "High CPU alert",
        "diagnosed_root_cause": None,
        "proposed_remediation": None,
        "is_destructive_action": False,
        "human_approved": False,
        "execution_status": "PENDING_DIAGNOSIS",
        "audit_trail": []
    }
    
    # Run to interrupt
    app_graph.invoke(initial_input, config=thread_config)
    
    # Resume without approval (human_approved remains False)
    final_state = app_graph.invoke(None, config=thread_config)
    
    assert final_state["execution_status"] == "REJECTED_BY_OPERATOR"
    assert any("Action execution blocked" in log for log in final_state["audit_trail"])
