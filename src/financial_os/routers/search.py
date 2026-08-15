"""Receipt search route — POST /api/v1/receipts/search.

The search term travels in the JSON body so it never enters infrastructure
request-URL logs (LOG-01, packet §5).  All responses are owner-scoped (IAM-01).
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from financial_os.auth.deps import OwnerDep
from financial_os.schemas.search import SearchReceiptsRequest, SearchReceiptsResponse
from financial_os.services.search import search_receipts

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.post("/receipts/search", response_model=SearchReceiptsResponse)
async def search_receipts_endpoint(
    body: SearchReceiptsRequest,
    request: Request,
    owner: OwnerDep,
) -> SearchReceiptsResponse:
    """Owner-only receipt search with keyset pagination and composable filters.

    The query body keeps merchant and item search terms out of URL-based logs.
    Fingerprints, hashes, and private identifiers are never returned.
    """
    async with request.app.state.session_factory() as session:
        return await search_receipts(
            session=session,
            owner=owner,
            request=body,
            settings=request.app.state.settings,
        )
