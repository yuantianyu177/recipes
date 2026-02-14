import io
import os
import uuid

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from PIL import Image

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass  # HEIC support optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import verify_token
from app.models.models import Recipe, RecipeImage

router = APIRouter(prefix="/api", tags=["upload"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif", ".avif", ".bmp", ".tiff", ".tif"}
ALLOWED_MIMETYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/heic", "image/heif", "image/avif", "image/bmp", "image/tiff"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/recipes/{recipe_id}/images")
async def upload_recipe_image(
    recipe_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    """Upload an image for a recipe."""
    # Verify recipe exists
    recipe = await db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    # Validate file type by extension or MIME type
    ext = os.path.splitext(file.filename or "")[1].lower()
    mime = (file.content_type or "").lower()
    if ext not in ALLOWED_EXTENSIONS and mime not in ALLOWED_MIMETYPES and not mime.startswith("image/"):
        raise HTTPException(status_code=400, detail=f"File type not allowed (ext={ext}, mime={mime})")

    # Read file content
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    # Convert all images to JPEG
    try:
        img = Image.open(io.BytesIO(content))
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True)
        content = buf.getvalue()
    except Exception:
        raise HTTPException(status_code=400, detail="Cannot process image file")

    # Save file as .jpg
    filename = f"{uuid.uuid4().hex}.jpg"
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)
    filepath = os.path.join(upload_dir, filename)
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    # Get current max sort_order
    result = await db.execute(
        select(RecipeImage).where(RecipeImage.recipe_id == recipe_id)
    )
    existing = result.scalars().all()
    sort_order = max((img.sort_order for img in existing), default=-1) + 1

    # Save to database
    image = RecipeImage(
        recipe_id=recipe_id,
        image_path=f"/uploads/{filename}",
        sort_order=sort_order,
    )
    db.add(image)
    await db.commit()
    await db.refresh(image)

    return {
        "id": image.id,
        "image_path": image.image_path,
        "sort_order": image.sort_order,
    }


@router.put("/recipes/{recipe_id}/images/reorder")
async def reorder_recipe_images(
    recipe_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    """Reorder images for a recipe. Expects { "image_ids": [3, 1, 2] }.
    Images not in the list will be deleted. Order follows list position."""
    recipe = await db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    image_ids = data.get("image_ids", [])

    # Fetch all current images for this recipe
    result = await db.execute(
        select(RecipeImage).where(RecipeImage.recipe_id == recipe_id)
    )
    existing = {img.id: img for img in result.scalars().all()}

    # Delete images not in the new list
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    for img_id, img in existing.items():
        if img_id not in image_ids:
            filename = os.path.basename(img.image_path)
            filepath = os.path.join(upload_dir, filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            await db.delete(img)

    # Update sort_order for remaining images
    for order, img_id in enumerate(image_ids):
        if img_id in existing:
            existing[img_id].sort_order = order

    await db.commit()
    return {"ok": True}


@router.delete("/images/{image_id}", status_code=204)
async def delete_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    """Delete a recipe image."""
    image = await db.get(RecipeImage, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    # Delete file from disk
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    filename = os.path.basename(image.image_path)
    filepath = os.path.join(upload_dir, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    await db.delete(image)
    await db.commit()
