from typing import TypedDict, List, Optional, Literal

class IncidentState(TypedDict):
    incident_id: str
    service_name: str
    raw_error_log: str
    diagnosed_root_cause: Optional[str]
    proposed_remediation: Optional[str]
    is_destructive_action: bool
    human_approved: bool
    execution_status: Literal["PENDING_DIAGNOSIS", "AWAITING_APPROVAL", "EXECUTED", "REJECTED_BY_OPERATOR"]
    audit_trail: List[str]
