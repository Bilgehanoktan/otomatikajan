from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pytest

from services.social_growth.config import MetaSettings
from services.social_growth.content_auditor import (
    AICompanyPostAuditor,
    AIReviewStatus,
    PostSnapshot,
    audit_posts,
)
from services.social_growth.meta_client import (
    GraphAPIError,
    GraphResponse,
    MetaGraphClient,
)

TEST_ACCESS_TOKEN = "access-token-secret-long-enough"
TEST_APP_SECRET = "app-secret-value-with-at-least-32-bytes"


class FakeTransport:
    def __init__(self, responses: list[GraphResponse]) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, Any]] = []

    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> GraphResponse:
        self.requests.append(
            {
                "method": method,
                "url": url,
                "params": params,
                "data": data,
                "headers": headers,
            }
        )
        return self.responses.pop(0)


class FakeReviewGateway:
    def __init__(self, response: str) -> None:
        self.response = response
        self.prompts: list[str] = []

    def review(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.response


class FailingReviewGateway:
    def review(self, prompt: str) -> str:
        raise RuntimeError("provider unavailable")


def make_settings() -> MetaSettings:
    return MetaSettings(
        account_id="17841400000000000",
        access_token=TEST_ACCESS_TOKEN,
        app_secret=TEST_APP_SECRET,
        verify_token="verify-token-value",
        api_version="v23.0",
    )


def make_post(
    media_id: str,
    minute: int,
    *,
    caption: str | None = None,
    comment_count: int | None = 0,
    alt_text: str | None = None,
) -> PostSnapshot:
    return PostSnapshot(
        media_id=media_id,
        permalink=f"https://www.instagram.com/ai_gucum_/p/{media_id}/",
        timestamp=datetime(2026, 7, 23, 20, minute, tzinfo=UTC),
        media_type="IMAGE",
        caption=caption,
        comment_count=comment_count,
        alt_text=alt_text,
    )


def test_meta_client_lists_recent_media_with_bounded_fields() -> None:
    transport = FakeTransport(
        [
            GraphResponse(
                200,
                {
                    "data": [
                        {
                            "id": "post-1",
                            "caption": "Caption",
                            "media_type": "IMAGE",
                            "permalink": "https://www.instagram.com/p/post-1/",
                            "timestamp": "2026-07-23T20:00:00+0000",
                            "comments_count": 2,
                        }
                    ],
                    "paging": {"next": "https://attacker.example/continue"},
                },
            )
        ]
    )
    client = MetaGraphClient(make_settings(), transport)

    media = client.list_recent_media(limit=6)

    assert media[0]["id"] == "post-1"
    assert len(transport.requests) == 1
    assert transport.requests[0]["method"] == "GET"
    assert transport.requests[0]["url"].endswith("/17841400000000000/media")
    assert transport.requests[0]["params"] == {
        "fields": "id,caption,media_type,permalink,timestamp,comments_count",
        "limit": 6,
    }

    with pytest.raises(ValueError, match="1 ile 25"):
        client.list_recent_media(limit=26)


def test_meta_client_rejects_malformed_media_data() -> None:
    client = MetaGraphClient(
        make_settings(),
        FakeTransport([GraphResponse(200, {"data": "not-a-list"})]),
    )

    with pytest.raises(GraphAPIError, match="data"):
        client.list_recent_media(limit=3)


def test_deterministic_audit_flags_observed_quality_failures() -> None:
    posts = [
        make_post(
            "post-1",
            0,
            alt_text=(
                "OpenIoiTahtoo Kayn Kaynaklı OpenAlol Tahtından İndiren "
                "fArac DeepSeekR Arac DeepSeek Fiyat Fiyat Ücretsiz Açık Kaynak"
            ),
        ),
        make_post("post-2", 35),
        make_post("post-3", 55),
    ]

    report = audit_posts(posts)
    codes = [finding.code for finding in report.findings]

    assert report.posts_checked == 3
    assert report.score < 50
    assert codes.count("MISSING_CAPTION") == 3
    assert codes.count("NO_COMMENT_SIGNAL") == 3
    assert "VISUAL_TEXT_RISK" in codes
    assert "POSTING_BURST_RISK" in codes
    assert report.input_fingerprint == audit_posts(posts).input_fingerprint


def test_missing_comment_count_stays_unknown() -> None:
    report = audit_posts(
        [
            make_post(
                "post-1",
                0,
                caption="Gerçek bir caption",
                comment_count=None,
                alt_text="Temiz ve kısa bir görsel açıklaması",
            )
        ]
    )

    codes = [finding.code for finding in report.findings]
    assert "COMMENT_SIGNAL_UNKNOWN" in codes
    assert "NO_COMMENT_SIGNAL" not in codes


def test_ai_company_review_accepts_only_grounded_schema() -> None:
    posts = [make_post("post-1", 0)]
    report = audit_posts(posts)
    gateway = FakeReviewGateway(
        json.dumps(
            {
                "summary": "Caption ve yorum sinyali eksik.",
                "priorities": [
                    {
                        "post_id": "post-1",
                        "issue_code": "MISSING_CAPTION",
                        "action": "Caption taslağı üret.",
                    }
                ],
                "draft_ideas": [
                    {
                        "hook": "Bu araç günde bir saat kazandırıyor",
                        "format": "6 slayt carousel",
                        "cta": "PROMPT yaz",
                    }
                ],
            },
            ensure_ascii=False,
        )
    )

    review = AICompanyPostAuditor(gateway).review(report)

    assert review.status is AIReviewStatus.REVIEWED
    assert review.summary == "Caption ve yorum sinyali eksik."
    assert len(gateway.prompts) == 1
    assert "post-1" in gateway.prompts[0]


def test_ai_company_review_accepts_json_code_fence_without_extra_text() -> None:
    report = audit_posts([make_post("post-1", 0)])
    response = """```json
{
  "summary": "Yalnız kanıtlı bulgular incelendi.",
  "priorities": [
    {
      "post_id": "post-1",
      "issue_code": "MISSING_CAPTION",
      "action": "Caption taslağı hazırla."
    }
  ],
  "draft_ideas": []
}
```"""

    review = AICompanyPostAuditor(FakeReviewGateway(response)).review(report)

    assert review.status is AIReviewStatus.REVIEWED


@pytest.mark.parametrize(
    "response",
    [
        "JSON olmayan yanıt",
        json.dumps(
            {
                "summary": "Bilinmeyen post",
                "priorities": [
                    {
                        "post_id": "unknown-post",
                        "issue_code": "MISSING_CAPTION",
                        "action": "Sil ve yeniden yayınla",
                    }
                ],
                "draft_ideas": [],
            }
        ),
        json.dumps(
            {
                "summary": "Bilinmeyen bulgu",
                "priorities": [
                    {
                        "post_id": "post-1",
                        "issue_code": "INVENTED_METRIC",
                        "action": "Skoru yükselt",
                    }
                ],
                "draft_ideas": [],
            }
        ),
    ],
)
def test_ai_company_review_fails_closed_for_ungrounded_output(response: str) -> None:
    report = audit_posts([make_post("post-1", 0)])

    review = AICompanyPostAuditor(FakeReviewGateway(response)).review(report)

    assert review.status is AIReviewStatus.BLOCKED_AI_REVIEW
    assert review.summary == ""
    assert review.priorities == ()
    assert review.draft_ideas == ()


def test_ai_company_review_fails_closed_when_provider_is_unavailable() -> None:
    report = audit_posts([make_post("post-1", 0)])

    review = AICompanyPostAuditor(FailingReviewGateway()).review(report)

    assert review.status is AIReviewStatus.BLOCKED_AI_REVIEW
    assert review.blocked_reason == "RuntimeError: provider unavailable"
