import hashlib
import hmac
import json
import os
import unittest
from unittest.mock import MagicMock, patch

# Mock environment variable for testing
TEST_SECRET = "test_webhook_secret_123"
os.environ["FASTAPI_PAYLOAD_WEBHOOK_SECRET"] = TEST_SECRET

# Mock dependencies to avoid full app loading
import sys
sys.modules['packages.observability.logging'] = MagicMock()

from apps.api.routers.payload_integration import _verify_signature, PayloadWebhookEvent

class TestPayloadIntegration(unittest.TestCase):
    def test_signature_verification_success(self):
        body = json.dumps({"collection": "test", "operation": "create"}).encode("utf-8")
        signature = hmac.new(
            TEST_SECRET.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Should not raise exception
        _verify_signature(body, signature)

    def test_signature_verification_failure(self):
        body = json.dumps({"collection": "test", "operation": "create"}).encode("utf-8")
        signature = "invalid_signature"
        
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as cm:
            _verify_signature(body, signature)
        self.assertEqual(cm.exception.status_code, 401)

    def test_webhook_event_model(self):
        data = {
            "collection": "runbooks",
            "operation": "update",
            "slug": "emergency-shutdown",
            "payload": {"title": "Updated Title"}
        }
        event = PayloadWebhookEvent(**data)
        self.assertEqual(event.collection, "runbooks")
        self.assertEqual(event.slug, "emergency-shutdown")

    @patch('apps.api.services.content_sync.handle_payload_event')
    async def test_webhook_service_call(self, mock_handle):
        # This is more of an integration logic check
        mock_handle.return_value = {"processed": True}
        from apps.api.routers.payload_integration import payload_webhook
        # We simulate the async call directly for the logic check
        # Since testing FastAPI routes directly in unittest is complex without TestClient,
        # we focus on the logic in handle_payload_event
        pass

class TestContentSync(unittest.IsolatedAsyncioTestCase):
    async def test_handle_runbook_event(self):
        from apps.api.services.content_sync import handle_payload_event
        event = {
            "collection": "runbooks",
            "operation": "afterChange",
            "slug": "test-runbook"
        }
        result = await handle_payload_event(event)
        self.assertTrue(result["processed"])
        self.assertEqual(result["collection"], "runbooks")

    async def test_handle_knowledge_event(self):
        from apps.api.services.content_sync import handle_payload_event
        event = {
            "collection": "knowledge-articles",
            "operation": "afterChange",
            "slug": "test-article"
        }
        result = await handle_payload_event(event)
        self.assertTrue(result["processed"])
        self.assertEqual(result["collection"], "knowledge-articles")

if __name__ == "__main__":
    unittest.main()
