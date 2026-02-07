"""TDD Phase 2.3: Ingredient CRUD API tests."""
import pytest


@pytest.mark.asyncio
async def test_ingredient_categories_crud(client, auth_headers):
    """Test ingredient category CRUD operations."""
    # Create
    resp = await client.post("/api/ingredients/categories", json={"name": "主料"}, headers=auth_headers)
    assert resp.status_code == 201
    cat_id = resp.json()["id"]
    assert resp.json()["name"] == "主料"
    # List
    resp = await client.get("/api/ingredients/categories")
    assert resp.status_code == 200
    assert any(c["id"] == cat_id for c in resp.json())
    # Delete
    resp = await client.delete(f"/api/ingredients/categories/{cat_id}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_create_ingredient(client, auth_headers):
    """POST /api/ingredients should create a new ingredient."""
    resp = await client.post("/api/ingredients", json={
        "name": "鸡蛋",
        "unit": "个",
        "calorie": 70.0,
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "鸡蛋"
    assert data["unit"] == "个"
    assert data["calorie"] == 70.0


@pytest.mark.asyncio
async def test_list_ingredients(client, auth_headers):
    """GET /api/ingredients should return all ingredients."""
    await client.post("/api/ingredients", json={"name": "盐", "unit": "克"}, headers=auth_headers)
    await client.post("/api/ingredients", json={"name": "糖", "unit": "克"}, headers=auth_headers)
    resp = await client.get("/api/ingredients")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_search_ingredients(client, auth_headers):
    """GET /api/ingredients?q=xxx should filter by name."""
    await client.post("/api/ingredients", json={"name": "花生油", "unit": "毫升"}, headers=auth_headers)
    await client.post("/api/ingredients", json={"name": "橄榄油", "unit": "毫升"}, headers=auth_headers)
    await client.post("/api/ingredients", json={"name": "酱油", "unit": "毫升"}, headers=auth_headers)
    resp = await client.get("/api/ingredients?q=油")
    data = resp.json()
    assert len(data) == 3
    for item in data:
        assert "油" in item["name"]


@pytest.mark.asyncio
async def test_update_ingredient(client, auth_headers):
    """PUT /api/ingredients/:id should update the ingredient."""
    create_resp = await client.post("/api/ingredients", json={
        "name": "牛肉", "unit": "克", "calorie": 250.0,
    }, headers=auth_headers)
    ing_id = create_resp.json()["id"]
    resp = await client.put(f"/api/ingredients/{ing_id}", json={
        "calorie": 260.0,
    }, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["calorie"] == 260.0


@pytest.mark.asyncio
async def test_delete_ingredient(client, auth_headers):
    """DELETE /api/ingredients/:id should remove the ingredient."""
    create_resp = await client.post("/api/ingredients", json={
        "name": "蘑菇", "unit": "克",
    }, headers=auth_headers)
    ing_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/ingredients/{ing_id}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_ingredient_in_use(client, auth_headers):
    """DELETE ingredient referenced by a recipe should return 409."""
    # Create ingredient
    ing_resp = await client.post("/api/ingredients", json={
        "name": "豆腐X", "unit": "块",
    }, headers=auth_headers)
    ing_id = ing_resp.json()["id"]
    # Create recipe using this ingredient
    await client.post("/api/recipes", json={
        "name": "麻婆豆腐",
        "ingredients": [{"ingredient_id": ing_id, "amount": "1"}],
    }, headers=auth_headers)
    # Try to delete ingredient - should fail
    resp = await client.delete(f"/api/ingredients/{ing_id}", headers=auth_headers)
    assert resp.status_code == 409
    assert "used by" in resp.json()["detail"]
