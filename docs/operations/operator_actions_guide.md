# Manual Override Policy

Manual overrides are high-risk actions that bypass automated safety checks. They must be logged and justified.

## 1. Allowed Overrides
- **Status Force-Set**: Changing a 'STUCK' workflow to 'PENDING' for a replay.
- **Context Correction**: Fixing a small typo in a task's context that would otherwise cause failure.
- **Budget Extension**: Temporarily increasing a project's budget by up to 20% in an emergency.

## 2. Forbidden Overrides
- **Bypassing Security Checks**: Manually forcing a step that failed RBAC.
- **Direct Database Manipulation**: Using raw SQL to change state without an audit trail. All actions must be via Control Plane or Service API.

## 3. Mandatory Audit
Every override MUST be accompanied by a `reason` comment. This comment is persisted in the `DomainEventLog` and linked to the `operator_id`.

---

# Operator Actions Guide

Step-by-step instructions for the Control Plane.

### How to Cancel a Workflow
1. Navigate to **Workflows**.
2. Select the running project.
3. Click the **Red 'Cancel' Button**.
4. Observe the worker logs to ensure the thread is terminated.

### How to handle a 'WAITING_APPROVAL' Step
1. Go to **Approvals Inbox**.
2. Review the input/output data and the risk score.
3. If valid, click **Approve**.
4. If invalid, click **Reject** and provide feedback for the agent to refine.

### How to trigger a Replay
1. Go to the project detail view.
2. Select the step you wish to restart from.
3. Ensure the current status allows replay.
4. Click **Replay**.
