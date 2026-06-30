import pytest

from apps.telegram_bot import polling


class FakeResponse:
    def __init__(self, status_code: int = 200, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {"status": "success"}
        self.text = text or str(self._payload)

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, response: FakeResponse):
        self.response = response
        self.calls = []

    async def post(self, url: str, *, json: dict, headers: dict, timeout: float):
        self.calls.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        return self.response


def test_parse_approval_callback_data_accepts_bilgeapi_format():
    parsed = polling.parse_approval_callback_data("approve:approval-123:tok12345")

    assert parsed == {
        "action": "approve",
        "approval_id": "approval-123",
        "short_token": "tok12345",
    }


@pytest.mark.parametrize("value", ["approve:missing-token", "reject", "noop:1:2", "approve::tok"])
def test_parse_approval_callback_data_rejects_invalid_values(value):
    assert polling.parse_approval_callback_data(value) is None


@pytest.mark.asyncio
async def test_forward_approval_callback_to_bilgeapi_webhook(monkeypatch):
    monkeypatch.setenv("BILGEAPI_ORIGIN", "http://bilgeapi:8100")
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "secret")
    client = FakeClient(FakeResponse())
    update_payload = {
        "callback_query": {
            "data": "reject:approval-123:tok12345",
            "from": {"id": 100, "username": "operator"},
            "message": {"chat": {"id": 100}},
        }
    }

    result = await polling.forward_approval_callback_to_bilgeapi(update_payload, client=client)

    assert result == (True, "REJECTED kararı kaydedildi.")
    assert client.calls == [
        {
            "url": "http://bilgeapi:8100/v1/telegram/webhook",
            "json": update_payload,
            "headers": {"X-Telegram-Bot-Api-Secret-Token": "secret"},
            "timeout": 15.0,
        }
    ]


@pytest.mark.asyncio
async def test_forward_approval_callback_does_not_post_invalid_payload():
    client = FakeClient(FakeResponse())

    result = await polling.forward_approval_callback_to_bilgeapi(
        {"callback_query": {"data": "approve:missing-token"}},
        client=client,
    )

    assert result == (False, "Geçersiz onay verisi.")
    assert client.calls == []
