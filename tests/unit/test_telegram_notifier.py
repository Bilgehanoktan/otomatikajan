import pytest

from apps.bilgeapi.integrations import telegram as bilgeapi_telegram
from apps.telegram_bot import bot as telegram_bot


def test_sanitize_telegram_log_text_redacts_bot_token(monkeypatch):
    monkeypatch.setattr(telegram_bot, "BOT_TOKEN", "123456:secret-token")

    text = telegram_bot.sanitize_telegram_log_text(
        "GET https://api.telegram.org/bot123456:secret-token/sendMessage failed"
    )

    assert "123456:secret-token" not in text
    assert "<telegram-token-redacted>" in text


def test_bilgeapi_telegram_log_redaction_redacts_bot_token():
    text = bilgeapi_telegram.sanitize_telegram_log_text(
        "GET https://api.telegram.org/bot123456:secret-token/sendMessage failed",
        "123456:secret-token",
    )

    assert "123456:secret-token" not in text
    assert "<telegram-token-redacted>" in text


@pytest.mark.asyncio
async def test_notify_event_uses_bilgeapi_callback_format_when_token_present(monkeypatch):
    captured = {}

    async def fake_send_to_all(self, text, reply_markup=None):
        captured["reply_markup"] = reply_markup

    monkeypatch.setattr(telegram_bot.TelegramNotifier, "_send_to_all", fake_send_to_all)

    notifier = telegram_bot.TelegramNotifier()
    await notifier.notify_event(
        "approval.needed",
        {
            "approval_id": "approval-123",
            "token": "abcdef1234567890",
            "title": "Needs approval",
        },
    )

    keyboard = captured["reply_markup"]["inline_keyboard"][0]
    assert keyboard[0]["callback_data"] == "approve:approval-123:abcdef12"
    assert keyboard[1]["callback_data"] == "reject:approval-123:abcdef12"


@pytest.mark.asyncio
async def test_notify_event_does_not_add_broken_legacy_buttons_without_token(monkeypatch):
    captured = {}

    async def fake_send_to_all(self, text, reply_markup=None):
        captured["reply_markup"] = reply_markup

    monkeypatch.setattr(telegram_bot.TelegramNotifier, "_send_to_all", fake_send_to_all)

    notifier = telegram_bot.TelegramNotifier()
    await notifier.notify_event(
        "approval.needed",
        {
            "request_id": "legacy-request",
            "title": "Needs approval",
        },
    )

    assert captured["reply_markup"] is None
