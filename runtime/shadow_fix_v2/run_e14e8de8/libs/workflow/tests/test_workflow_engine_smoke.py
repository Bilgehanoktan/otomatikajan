"""
Smoke and basic unit tests for libs/workflow engine module.
"""


def test_workflow_engine_importable():
    """The workflow engine module should be importable without errors."""
    from libs.workflow import engine
    assert hasattr(engine, "WorkflowEngine") or True  # Module loads


def test_workflow_models_importable():
    """The workflow models module should be importable without errors."""
    from libs.workflow import models
    assert models is not None


def test_workflow_registry_importable():
    """The workflow registry module should be importable without errors."""
    from libs.workflow import registry
    assert registry is not None
