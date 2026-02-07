"""TDD Phase 2.4: Tag CRUD API tests."""
import pytest


@pytest.mark.asyncio
async def test_create_tag(client, auth_headers):
    """POST /api/tags should create a new tag."""
    # First create a tag category
    cat_resp = await client.post("/api/tags/categories", json={"name": "菜系"}, headers=auth_headers)
    cat_id = cat_resp.json()["id"]
    resp = await client.post("/api/tags", json={
        "name": "川菜",
        "category_id": cat_id,
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "川菜"
    assert data["category"] == "菜系"
    assert data["category_id"] == cat_id


@pytest.mark.asyncio
async def test_list_tags(client, auth_headers):
    """GET /api/tags should return all tags."""
    cat_resp = await client.post("/api/tags/categories", json={"name": "场景B"}, headers=auth_headers)
    cat_id = cat_resp.json()["id"]
    await client.post("/api/tags", json={"name": "午餐", "category_id": cat_id}, headers=auth_headers)
    await client.post("/api/tags", json={"name": "晚餐", "category_id": cat_id}, headers=auth_headers)
    resp = await client.get("/api/tags")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_update_tag(client, auth_headers):
    """PUT /api/tags/:id should update the tag."""
    cat_resp = await client.post("/api/tags/categories", json={"name": "口味C"}, headers=auth_headers)
    cat_id = cat_resp.json()["id"]
    create_resp = await client.post("/api/tags", json={
        "name": "辣味", "category_id": cat_id,
    }, headers=auth_headers)
    tag_id = create_resp.json()["id"]
    resp = await client.put(f"/api/tags/{tag_id}", json={
        "name": "麻辣",
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "麻辣"


@pytest.mark.asyncio
async def test_delete_tag(client, auth_headers):
    """DELETE /api/tags/:id should remove an unused tag."""
    create_resp = await client.post("/api/tags", json={
        "name": "临时标签",
    }, headers=auth_headers)
    tag_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/tags/{tag_id}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_tag_in_use(client, auth_headers):
    """DELETE tag referenced by a recipe should return 409."""
    # Create tag
    tag_resp = await client.post("/api/tags", json={
        "name": "已使用标签",
    }, headers=auth_headers)
    tag_id = tag_resp.json()["id"]
    # Create recipe with this tag
    await client.post("/api/recipes", json={
        "name": "测试菜谱",
        "tag_ids": [tag_id],
    }, headers=auth_headers)
    # Try to delete tag - should fail
    resp = await client.delete(f"/api/tags/{tag_id}", headers=auth_headers)
    assert resp.status_code == 409
    assert "used by" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_tag_categories_crud(client, auth_headers):
    """Test tag category CRUD operations."""
    # Create
    resp = await client.post("/api/tags/categories", json={"name": "测试分类"}, headers=auth_headers)
    assert resp.status_code == 201
    cat_id = resp.json()["id"]
    assert resp.json()["name"] == "测试分类"
    # List
    resp = await client.get("/api/tags/categories")
    assert resp.status_code == 200
    assert any(c["id"] == cat_id for c in resp.json())
    # Delete
    resp = await client.delete(f"/api/tags/categories/{cat_id}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_tag_category_in_use(client, auth_headers):
    """DELETE tag category referenced by a tag should return 409."""
    cat_resp = await client.post("/api/tags/categories", json={"name": "被引用分类"}, headers=auth_headers)
    cat_id = cat_resp.json()["id"]
    await client.post("/api/tags", json={"name": "引用标签", "category_id": cat_id}, headers=auth_headers)
    resp = await client.delete(f"/api/tags/categories/{cat_id}", headers=auth_headers)
    assert resp.status_code == 409
