def test_workflow_api_openapi_schema_builds():
    from services.workflow_api.main import app

    schema = app.openapi()

    assert schema["info"]["title"]
    assert "/api/v1/project-factory/portfolio/search" in schema["paths"]
