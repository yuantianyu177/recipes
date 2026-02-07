"""TDD Phase 2.2: Recipe CRUD API tests."""
import pytest


@pytest.mark.asyncio
async def test_create_recipe(client, auth_headers):
    """POST /api/recipes should create a new recipe."""
    resp = await client.post("/api/recipes", json={
        "name": "西红柿炒鸡蛋",
        "description": "<p>Classic dish</p>",
        "steps": "<p>Step 1: Scramble eggs</p>",
        "tips": "Use fresh tomatoes",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "西红柿炒鸡蛋"
    assert data["id"] > 0
    # Check that created_at and updated_at are present
    assert data.get("created_at") is not None
    assert data.get("updated_at") is not None


@pytest.mark.asyncio
async def test_create_recipe_no_auth(client):
    """POST /api/recipes without auth should return 401/403."""
    resp = await client.post("/api/recipes", json={"name": "No Auth"})
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_list_recipes(client, auth_headers):
    """GET /api/recipes should return a list."""
    await client.post("/api/recipes", json={"name": "Recipe A"}, headers=auth_headers)
    await client.post("/api/recipes", json={"name": "Recipe B"}, headers=auth_headers)
    resp = await client.get("/api/recipes")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_recipe(client, auth_headers):
    """GET /api/recipes/:id should return recipe detail."""
    create_resp = await client.post("/api/recipes", json={
        "name": "Detail Test",
        "description": "Test desc",
    }, headers=auth_headers)
    recipe_id = create_resp.json()["id"]
    resp = await client.get(f"/api/recipes/{recipe_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Detail Test"
    assert data["description"] == "Test desc"


@pytest.mark.asyncio
async def test_get_recipe_not_found(client):
    """GET /api/recipes/999999 should return 404."""
    resp = await client.get("/api/recipes/999999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_recipe(client, auth_headers):
    """PUT /api/recipes/:id should update recipe fields."""
    create_resp = await client.post("/api/recipes", json={"name": "Old Name"}, headers=auth_headers)
    recipe_id = create_resp.json()["id"]
    resp = await client.put(f"/api/recipes/{recipe_id}", json={
        "name": "New Name",
        "tips": "Updated tips",
    }, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "New Name"
    assert data["tips"] == "Updated tips"


@pytest.mark.asyncio
async def test_delete_recipe(client, auth_headers):
    """DELETE /api/recipes/:id should remove the recipe."""
    create_resp = await client.post("/api/recipes", json={"name": "To Delete"}, headers=auth_headers)
    recipe_id = create_resp.json()["id"]
    resp = await client.delete(f"/api/recipes/{recipe_id}", headers=auth_headers)
    assert resp.status_code == 204
    get_resp = await client.get(f"/api/recipes/{recipe_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_recipe_with_tags(client, auth_headers):
    """POST /api/recipes with tag_ids should associate tags."""
    cat_resp = await client.post("/api/tags/categories", json={"name": "场景X"}, headers=auth_headers)
    cat_id = cat_resp.json()["id"]
    tag1 = await client.post("/api/tags", json={"name": "早餐A", "category_id": cat_id}, headers=auth_headers)
    tag2 = await client.post("/api/tags", json={"name": "快手菜A", "category_id": cat_id}, headers=auth_headers)
    t1_id = tag1.json()["id"]
    t2_id = tag2.json()["id"]
    resp = await client.post("/api/recipes", json={
        "name": "Tagged Recipe",
        "tag_ids": [t1_id, t2_id],
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    tag_names = {t["name"] for t in data["tags"]}
    assert "早餐A" in tag_names
    assert "快手菜A" in tag_names


@pytest.mark.asyncio
async def test_create_recipe_with_ingredients(client, auth_headers):
    """POST /api/recipes with ingredients should associate them."""
    # Create ingredient category, then ingredient with that category
    cat_resp = await client.post("/api/ingredients/categories", json={"name": "主料"}, headers=auth_headers)
    cat_id = cat_resp.json()["id"]
    ing = await client.post("/api/ingredients", json={
        "name": "西红柿B",
        "unit": "个",
        "calorie": 18.0,
        "category_id": cat_id,
    }, headers=auth_headers)
    ing_id = ing.json()["id"]
    resp = await client.post("/api/recipes", json={
        "name": "With Ingredients",
        "ingredients": [
            {"ingredient_id": ing_id, "amount": "2"}
        ],
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["ingredients"]) == 1
    assert data["ingredients"][0]["amount"] == "2"
    assert data["ingredients"][0]["ingredient_name"] == "西红柿B"
    assert data["ingredients"][0]["category"] == "主料"
    assert data["ingredients"][0]["category_id"] == cat_id
