import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from tasks.deerflow_tasks import run_deerflow_task

from integrations.deerflow_bridge import DeerFlowBridgeClient

class MockTask:
    def __init__(self):
        self.request = MagicMock()
        self.request.retries = 0

@patch("tasks.deerflow_tasks.AsyncSessionLocal")
@patch("db.repository.ProjectRepository.get")
@patch("db.repository.ProjectRepository.mark_started")
@patch("db.repository.ProjectRepository.mark_completed")
@patch("integrations.deerflow_bridge.DeerFlowBridgeClient.run")
def test_deerflow_task_unit(mock_run, mock_completed, mock_started, mock_get, mock_db):
    """Celery görevinin bridge client'ı doğru çağırdığını test eder (Unit)."""
    # Mocklar
    mock_run.return_value = {"status": "success", "result": "mock_result"}
    
    p_mock = MagicMock()
    p_mock.status = MagicMock()
    p_mock.status.value = "pending"
    p_mock.id = "00000000-0000-0000-0000-000000000000"
    mock_get.return_value = p_mock
    
    # Asenkron Context Manager Mock
    mock_session = MagicMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None
    mock_db.return_value = mock_session
    
    mock_self = MockTask()
    # run_deerflow_task'ı positional args ile çağırarak TypeError'dan kaçın (self + 3 args)
    result = run_deerflow_task.run(
        mock_self,
        "00000000-0000-0000-0000-000000000000",
        "title",
        "description"
    )
    
    assert result["status"] == "success"
    assert mock_run.called

@pytest.mark.asyncio
async def test_deerflow_integration_mock_bridge():
    """Entegrasyon katmanının (integrations/deerflow_bridge.py) mantığını test eder."""
    client = DeerFlowBridgeClient(base_url="http://mock-bridge")
    
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"status": "success", "result": "ok"}
        )
        mock_post.return_value.raise_for_status = MagicMock()
        
        result = await client.run(thread_id="test", prompt="hi")
    assert result["status"] == "success"
    assert result["result"] == "ok"

@patch("tasks.deerflow_tasks.AsyncSessionLocal")
@patch("db.repository.ProjectRepository.get")
@patch("db.repository.ProjectRepository.mark_started")
@patch("db.repository.ProjectRepository.mark_completed")
@patch("db.repository.TaskLogRepository.write")
@patch("integrations.deerflow_bridge.DeerFlowBridgeClient.stream_run")
def test_deerflow_streaming_task_unit(mock_stream, mock_log_write, mock_completed, mock_started, mock_get, mock_db):
    """Streaming Celery görevinin bridge'i doğru tükettiğini test eder."""
    from tasks.deerflow_tasks import run_deerflow_streaming_task
    
    # Mock Stream Generator
    async def mock_gen(*args, **kwargs):
        yield {"event": "messages-tuple", "data": {"type": "ai", "content": "thinking..."}}
        yield {"event": "messages-tuple", "data": {"type": "ai", "content": "final answer"}}
        
    mock_stream.return_value = mock_gen()
    
    p_mock = MagicMock()
    p_mock.status = "pending"
    p_mock.id = "00000000-0000-0000-0000-000000000000"
    mock_get.return_value = p_mock
    
    mock_session = MagicMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.commit = AsyncMock() # Fix: make commit awaitable
    mock_db.return_value = mock_session
    
    mock_self = MockTask()
    result = run_deerflow_streaming_task.run(
        mock_self,
        "00000000-0000-0000-0000-000000000000",
        "title",
        "description"
    )
    
    assert result["status"] == "success"
    assert mock_stream.called
    assert mock_log_write.called

@pytest.mark.asyncio
async def test_deerflow_bridge_streaming_logic():
    """Bridge client streaming (SSE) mantığını mock httpx ile test eder."""
    from integrations.deerflow_bridge import DeerFlowBridgeClient
    client = DeerFlowBridgeClient(base_url="http://mock-bridge")
    
    mock_lines = [
        b"event: message\n",
        b"data: {\"content\": \"hello\"}\n",
        b"\n",
        b"event: end\n",
        b"data: {\"status\": \"done\"}\n",
        b"\n"
    ]
    
    with patch("httpx.AsyncClient.stream") as mock_stream:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        
        async def aiter_lines():
            for line in mock_lines:
                yield line.decode()
                
        mock_resp.aiter_lines = aiter_lines
        mock_stream.return_value.__aenter__.return_value = mock_resp
        
        events = []
        async for ev in client.stream_run(thread_id="t1", prompt="hi"):
            events.append(ev)
            
        assert len(events) == 2
        assert events[0]["event"] == "message"
        assert events[1]["event"] == "end"
