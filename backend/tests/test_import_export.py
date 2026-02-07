"""TDD Phase 2.7: Import/Export tests."""
import pytest
import io
import zipfile
import json


@pytest.mark.asyncio
async def test_export_recipe(client, auth_headers):
    """GET /api/recipes/:id/export should return a ZIP file."""
    # Create a recipe with data
    tag_resp = await client.post("/api/tags", json={"name": "导出标签", "category": "test"}, headers=auth_headers)
    tag_id = tag_resp.json()["id"]
    ing_resp = await client.post("/api/ingredients", json={"name": "导出食材", "unit": "克"}, headers=auth_headers)
    ing_id = ing_resp.json()["id"]
    recipe_resp = await client.post("/api/recipes", json={
        "name": "导出测试菜谱",
        "description": "<p>Test export</p>",
        "steps": "<p>Step 1</p>",
        "tips": "Tip!",
        "tag_ids": [tag_id],
        "ingredients": [{"ingredient_id": ing_id, "amount": "100"}],
    }, headers=auth_headers)
    recipe_id = recipe_resp.json()["id"]

    # Export
    resp = await client.get(f"/api/recipes/{recipe_id}/export", headers=auth_headers)
    assert resp.status_code == 200
    assert "application/zip" in resp.headers["content-type"]

    # Verify ZIP contents
    buf = io.BytesIO(resp.content)
    with zipfile.ZipFile(buf) as zf:
        names = zf.namelist()
        assert "recipe.json" in names
        recipe_data = json.loads(zf.read("recipe.json"))
        assert recipe_data["recipe"]["name"] == "导出测试菜谱"
        assert "导出标签" in recipe_data["recipe"]["tags"]
        assert recipe_data["recipe"]["ingredients"][0]["name"] == "导出食材"


@pytest.mark.asyncio
async def test_import_recipe(client, auth_headers):
    """POST /api/recipes/import should create a recipe from ZIP."""
    # Build a valid ZIP
    recipe_data = {
        "version": "1.0",
        "recipe": {
            "name": "导入测试菜谱",
            "description": "<p>Imported</p>",
            "steps": "<p>Imported steps</p>",
            "tips": "Import tip",
            "images": [],
            "ingredients": [
                {"name": "导入食材", "amount": "50", "category": "主料"}
            ],
            "tags": ["导入标签"],
        }
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("recipe.json", json.dumps(recipe_data, ensure_ascii=False))
    buf.seek(0)

    resp = await client.post(
        "/api/recipes/import",
        files={"file": ("recipe.zip", buf, "application/zip")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "recipe_ids" in data
    assert data["count"] == 1

    # Verify the imported recipe
    get_resp = await client.get(f"/api/recipes/{data['recipe_ids'][0]}")
    assert get_resp.status_code == 200
    recipe = get_resp.json()
    assert recipe["name"] == "导入测试菜谱"
    assert len(recipe["tags"]) == 1
    assert recipe["tags"][0]["name"] == "导入标签"
    assert len(recipe["ingredients"]) == 1
    assert recipe["ingredients"][0]["ingredient_name"] == "导入食材"


@pytest.mark.asyncio
async def test_import_invalid_zip(client, auth_headers):
    """POST /api/recipes/import with non-ZIP should return 400."""
    fake = io.BytesIO(b"not a zip")
    resp = await client.post(
        "/api/recipes/import",
        files={"file": ("bad.zip", fake, "application/zip")},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_roundtrip_export_import(client, auth_headers):
    """Export then import should create a copy of the recipe."""
    # Create original
    recipe_resp = await client.post("/api/recipes", json={
        "name": "往返测试",
        "description": "Round-trip test",
    }, headers=auth_headers)
    original_id = recipe_resp.json()["id"]

    # Export
    export_resp = await client.get(f"/api/recipes/{original_id}/export", headers=auth_headers)
    assert export_resp.status_code == 200

    # Import
    zip_buf = io.BytesIO(export_resp.content)
    import_resp = await client.post(
        "/api/recipes/import",
        files={"file": ("recipe.zip", zip_buf, "application/zip")},
        headers=auth_headers,
    )
    assert import_resp.status_code == 200
    new_id = import_resp.json()["recipe_ids"][0]
    assert new_id != original_id

    # Verify imported recipe matches
    get_resp = await client.get(f"/api/recipes/{new_id}")
    assert get_resp.json()["name"] == "往返测试"
