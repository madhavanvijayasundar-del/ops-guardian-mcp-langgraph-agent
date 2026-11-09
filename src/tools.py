from typing import Dict

# Simulated Kubernetes Cluster State (Azure AKS)
MOCK_K8S_ENVIRONMENT = {
    "payment-service": {
        "status": "CrashLoopBackOff",
        "restarts": 14,
        "last_log": "java.lang.OutOfMemoryError: Container memory limit (512Mi) exceeded. OOMKilled by Linux cgroups."
    },
    "auth-service": {
        "status": "Running",
        "restarts": 0,
        "last_log": "All token validation requests healthy."
    }
}

def mcp_read_pod_logs(service_name: str) -> str:
    """Read-only MCP tool: inspects container logs."""
    service = MOCK_K8S_ENVIRONMENT.get(service_name)
    if not service:
        return f"Service {service_name} not found in cluster."
    return f"Status: {service['status']} | Restarts: {service['restarts']} | Log: {service['last_log']}"

def mcp_read_terraform_runbook(issue_type: str) -> str:
    """Read-only MCP tool: retrieves verified infrastructure runbooks."""
    if "OOMKilled" in issue_type or "memory" in issue_type.lower():
        return "Remediation: Increase pod memory limit from 512Mi to 1024Mi and trigger rollout restart."
    return "Remediation: Standard rolling restart required."

def mcp_execute_kubectl_remediation(service_name: str, command: str) -> Dict[str, str]:
    """Privileged write tool: executes remediation (Requires Human Approval)."""
    if service_name in MOCK_K8S_ENVIRONMENT:
        MOCK_K8S_ENVIRONMENT[service_name]["status"] = "Running"
        MOCK_K8S_ENVIRONMENT[service_name]["restarts"] = 0
        return {"status": "SUCCESS", "message": f"Applied '{command}' to {service_name}. Cluster returned to healthy."}
    return {"status": "FAILED", "message": f"Target service {service_name} unreachable."}
