from fastapi import APIRouter, Depends, Query

from app.core.auth import verify_token
from app.services.search import search_recipes, update_synonyms, get_synonyms, setup_index

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def search(
    q: str = Query("", description="Search keyword"),
    tag: str = Query("", description="Tag filter, e.g. '川菜'"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Search recipes via MeiliSearch."""
    tag_filter = f'tags = "{tag}"' if tag else None
    result = search_recipes(query=q, tag_filter=tag_filter, limit=limit, offset=offset)
    return {
        "hits": result.get("hits", []),
        "total": result.get("estimatedTotalHits", 0),
    }


@router.post("/setup")
async def setup_search_index(_=Depends(verify_token)):
    """Initialize/configure MeiliSearch index settings."""
    setup_index()
    return {"status": "ok"}


@router.get("/synonyms")
async def list_synonyms(_=Depends(verify_token)):
    """Get current synonym groups."""
    try:
        return get_synonyms()
    except Exception:
        return {}


@router.put("/synonyms")
async def set_synonyms(synonyms: dict[str, list[str]], _=Depends(verify_token)):
    """Update synonym groups. Example: {"番茄": ["西红柿"]}"""
    update_synonyms(synonyms)
    return {"status": "ok"}
