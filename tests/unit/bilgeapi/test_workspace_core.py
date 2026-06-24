import os
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from apps.bilgeapi.core.workspace import WorkspaceManager
from apps.bilgeapi.core.settings_loader import SettingsLoader
from apps.bilgeapi.core.discovery import SystemDiscovery
from apps.bilgeapi.core.system_profile import SystemProfiler
from apps.bilgeapi.core.health_score import HealthScorer

def test_workspace_core_lifecycle():
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir).resolve()
        
        # 1. Create a dummy marker to simulate project root
        (tmp_path / "pyproject.toml").write_text("[tool.poetry]", encoding="utf-8")
        (tmp_path / ".gitignore").write_text("node_modules", encoding="utf-8")
        
        # Initialize workspace under root
        manager = WorkspaceManager(start_path=str(tmp_path))
        assert manager.project_root == tmp_path
        assert manager.workspace_dir == tmp_path / ".bilgeapi"
        
        created = manager.initialize_workspace()
        assert created[".bilgeapi"] == str(tmp_path / ".bilgeapi")
        assert (tmp_path / ".bilgeapi" / "logs").is_dir()
        assert (tmp_path / ".bilgeapi" / "system.yaml").is_file()
        
        # 2. Check settings loader
        loader = SettingsLoader(manager.workspace_dir)
        system_cfg = loader.get_system_config()
        assert system_cfg["system_name"] == "Auto-Discovered Project"
        
        # 3. Check SystemDiscovery
        discovery = SystemDiscovery(tmp_path)
        project_type = discovery.discover_project_type()
        assert project_type == "Python"
        
        commands = discovery.discover_commands(project_type)
        assert "test" in commands
        
        # 4. Check SystemProfiler
        profiler = SystemProfiler(tmp_path, manager.workspace_dir)
        profile = profiler.build_profile()
        assert profile["system_name"] == "Auto-Discovered Project"
        assert profile["project_type"] == "Python"
        assert (tmp_path / ".bilgeapi" / "system.yaml").exists()
        
        # 5. Check HealthScorer
        scorer = HealthScorer(tmp_path, manager.workspace_dir)
        health = scorer.calculate_score(profile)
        assert "score" in health
        assert "grade" in health
        assert health["score"] >= 80.0


def test_system_profile_endpoint(test_client):
    response = test_client.get("/v1/system/profile")
    assert response.status_code == 200
    data = response.json()
    assert "profile" in data
    assert "health" in data
    assert "score" in data["health"]


def test_ollama_provider_settings_loader():
    from apps.bilgeapi.llm.ollama_provider import OllamaProvider
    provider = OllamaProvider()
    assert provider.primary_model == "llama3.1:8b"
    assert provider.secondary_model == "mistral:7b"
    assert provider.tertiary_model == "gemma3:4b"
    assert provider.timeout == 60.0

