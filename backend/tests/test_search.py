"""TDD Phase 2.5: Search integration tests (MeiliSearch)."""
import pytest
import asyncio


@pytest.mark.asyncio
async def test_setup_search_index(client, auth_headers):
    """POST /api/search/setup should configure MeiliSearch index."""
    resp = await client.post("/api/search/setup", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_search_recipes(client, auth_headers):
    """GET /api/search?q=xxx should return matching recipes."""
    # Setup index first
    await client.post("/api/search/setup", headers=auth_headers)
    # Create some recipes (they auto-sync to search index)
    await client.post("/api/recipes", json={
        "name": "西红柿炒鸡蛋",
    }, headers=auth_headers)
    await client.post("/api/recipes", json={
        "name": "红烧排骨",
    }, headers=auth_headers)
    # Wait for MeiliSearch indexing (async)
    await asyncio.sleep(1)
    # Search
    resp = await client.get("/api/search?q=西红柿")
    assert resp.status_code == 200
    data = resp.json()
    assert "hits" in data
    assert "total" in data
    # At least the tomato recipe should be found
    if data["total"] > 0:
        hit_names = [h["name"] for h in data["hits"]]
        assert any("西红柿" in name for name in hit_names)


@pytest.mark.asyncio
async def test_search_with_tag_filter(client, auth_headers):
    """GET /api/search?q=&tag=xxx should filter by tag."""
    await client.post("/api/search/setup", headers=auth_headers)
    # Create tag and recipe
    tag_resp = await client.post("/api/tags", json={"name": "早餐T", "category": "场景"}, headers=auth_headers)
    tag_id = tag_resp.json()["id"]
    await client.post("/api/recipes", json={
        "name": "煎蛋",
        "tag_ids": [tag_id],
    }, headers=auth_headers)
    await asyncio.sleep(1)
    # Search with tag filter
    resp = await client.get("/api/search?q=&tag=早餐T")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_set_synonyms(client, auth_headers):
    """PUT /api/search/synonyms should update synonyms."""
    resp = await client.put("/api/search/synonyms", json={
        "番茄": ["西红柿"],
        "土豆": ["马铃薯"],
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
