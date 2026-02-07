"""TDD Phase 2.6: Image upload API tests."""
import pytest
import io


@pytest.mark.asyncio
async def test_upload_image(client, auth_headers):
    """POST /api/recipes/:id/images should upload and associate an image."""
    # Create a recipe first
    recipe_resp = await client.post("/api/recipes", json={"name": "图片测试"}, headers=auth_headers)
    recipe_id = recipe_resp.json()["id"]

    # Create a fake image file
    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    resp = await client.post(
        f"/api/recipes/{recipe_id}/images",
        files={"file": ("test.png", fake_image, "image/png")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["image_path"].startswith("/uploads/")
    assert data["sort_order"] == 0


@pytest.mark.asyncio
async def test_upload_multiple_images(client, auth_headers):
    """Uploading multiple images should increment sort_order."""
    recipe_resp = await client.post("/api/recipes", json={"name": "多图测试"}, headers=auth_headers)
    recipe_id = recipe_resp.json()["id"]

    for i in range(3):
        fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
        resp = await client.post(
            f"/api/recipes/{recipe_id}/images",
            files={"file": (f"img{i}.png", fake_image, "image/png")},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["sort_order"] == i


@pytest.mark.asyncio
async def test_upload_invalid_type(client, auth_headers):
    """Uploading non-image file should return 400."""
    recipe_resp = await client.post("/api/recipes", json={"name": "格式测试"}, headers=auth_headers)
    recipe_id = recipe_resp.json()["id"]

    fake_file = io.BytesIO(b"not an image")
    resp = await client.post(
        f"/api/recipes/{recipe_id}/images",
        files={"file": ("test.txt", fake_file, "text/plain")},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_delete_image(client, auth_headers):
    """DELETE /api/images/:id should remove the image."""
    recipe_resp = await client.post("/api/recipes", json={"name": "删除图片"}, headers=auth_headers)
    recipe_id = recipe_resp.json()["id"]

    fake_image = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 50)
    upload_resp = await client.post(
        f"/api/recipes/{recipe_id}/images",
        files={"file": ("del.png", fake_image, "image/png")},
        headers=auth_headers,
    )
    image_id = upload_resp.json()["id"]

    resp = await client.delete(f"/api/images/{image_id}", headers=auth_headers)
    assert resp.status_code == 204
