from __future__ import annotations


STEP_STATUSES = {
    "PENDING",
    "READY",
    "RUNNING",
    "WAITING_APPROVAL",
    "SUCCEEDED",
    "FAILED",
    "RETRYING",
    "SKIPPED",
    "BLOCKED",
    "CANCELLED",
    "ROLLED_BACK",
}

WORKFLOW_STATUSES = {
    "CREATED",
    "RUNNING",
    "WAITING_HUMAN",
    "FAILED",
    "BLOCKED",
    "DRAFT_PR_READY",
    "CANARY_RUNNING",
    "PROMOTED",
    "ROLLED_BACK",
    "COMPLETED",
}

VALID_STEP_TRANSITIONS = {
    "PENDING": {"READY", "SKIPPED", "CANCELLED"},
    "READY": {"RUNNING", "SKIPPED", "BLOCKED", "CANCELLED"},
    "RUNNING": {"SUCCEEDED", "FAILED", "WAITING_APPROVAL", "BLOCKED", "CANCELLED"},
    "FAILED": {"RETRYING", "BLOCKED"},
    "RETRYING": {"READY", "RUNNING", "FAILED", "BLOCKED"},
    "WAITING_APPROVAL": {"SUCCEEDED", "BLOCKED", "CANCELLED"},
    "SUCCEEDED": set(),
    "SKIPPED": set(),
    "BLOCKED": set(),
    "CANCELLED": set(),
    "ROLLED_BACK": set(),
}

VALID_WORKFLOW_TRANSITIONS = {
    "CREATED": {"RUNNING", "FAILED", "BLOCKED"},
    "RUNNING": {"WAITING_HUMAN", "FAILED", "BLOCKED", "DRAFT_PR_READY", "COMPLETED"},
    "WAITING_HUMAN": {"RUNNING", "BLOCKED", "DRAFT_PR_READY"},
    "DRAFT_PR_READY": {"COMPLETED"},
    "CANARY_RUNNING": {"PROMOTED", "ROLLED_BACK", "FAILED"},
    "PROMOTED": {"COMPLETED"},
    "FAILED": set(),
    "BLOCKED": set(),
    "ROLLED_BACK": set(),
    "COMPLETED": set(),
}


def can_transition_step(current: str, target: str) -> bool:
    if current not in STEP_STATUSES or target not in STEP_STATUSES:
        return False
    return target in VALID_STEP_TRANSITIONS[current]


def transition_step(current: str, target: str) -> str:
    if not can_transition_step(current, target):
        raise ValueError(f"Invalid step transition: {current} -> {target}")
    return target


def can_transition_workflow(current: str, target: str) -> bool:
    if current not in WORKFLOW_STATUSES or target not in WORKFLOW_STATUSES:
        return False
    return target in VALID_WORKFLOW_TRANSITIONS[current]


def transition_workflow(current: str, target: str) -> str:
    if not can_transition_workflow(current, target):
        raise ValueError(f"Invalid workflow transition: {current} -> {target}")
    return target

