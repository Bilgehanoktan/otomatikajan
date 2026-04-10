import os
from typing import Any, Optional

import httpx
from packages.observability.logging import get_logger

logger = get_logger("services.content_sync")


async def fetch_payload_document(collection: str, id_or_slug: str) -> Optional[dict[str, Any]]:
    """
    Fetches a document from the Payload REST API.
    Used for further processing or if extra verification is needed.
    """
    payload_base_url = os.getenv("PAYLOAD_BASE_URL", "http://localhost:3100")
    
    # Try slug first if it looks like one, otherwise ID
    url = f"{payload_base_url}/api/{collection}"
    
    params = {
        "where[slug][equals]": id_or_slug,
        "limit": 1,
        "depth": 1,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            docs = data.get("docs", [])
            return docs[0] if docs else None
    except Exception as exc:
        logger.warning(f"Payload fetch failed | collection={collection} target={id_or_slug} err={exc}")
        return None


async def handle_payload_event(event: dict[str, Any]) -> dict[str, Any]:
    """
    Processes a webhook event from Payload.
    Currently logs the event and prepares for future cache/state invalidations.
    """
    collection = event.get("collection")
    operation = event.get("operation")
    slug = event.get("slug")
    doc_id = event.get("docId")

    logger.info(f"Syncing Payload content | collection={collection} operation={operation} slug={slug}")

    # Specific logic per collection can be added here
    if collection == "runbooks":
        logger.info(f"Runbook updated: {slug or doc_id}. Ready for engine refresh.")
        # Trigger any internal system refresh if necessary
        
    elif collection == "knowledge-articles":
        logger.info(f"Knowledge article updated: {slug or doc_id}. Updating help center index.")

    return {
        "processed": True,
        "collection": collection,
        "operation": operation,
        "slug": slug,
    }
