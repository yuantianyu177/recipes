import io
import zipfile

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth import verify_token
from app.models.models import Recipe
from app.services.import_export import export_recipe, import_recipe

router = APIRouter(prefix="/api", tags=["import_export"])


@router.get("/recipes/{recipe_id}/export")
async def export_recipe_zip(
    recipe_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    """Export a single recipe as a ZIP file."""
    buf = await export_recipe(recipe_id, db)
    if buf is None:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=recipe_{recipe_id}.zip"},
    )


@router.post("/recipes/export-batch")
async def export_batch(
    data: dict,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    """Export multiple recipes as a single ZIP containing individual recipe ZIPs."""
    recipe_ids = data.get("recipe_ids", [])
    if not recipe_ids:
        raise HTTPException(status_code=400, detail="No recipe IDs provided")

    # Get recipe names for ZIP entry naming
    result = await db.execute(select(Recipe).where(Recipe.id.in_(recipe_ids)))
    recipes = {r.id: r.name for r in result.scalars().all()}

    outer_buf = io.BytesIO()
    with zipfile.ZipFile(outer_buf, "w", zipfile.ZIP_DEFLATED) as outer_zip:
        for rid in recipe_ids:
            buf = await export_recipe(rid, db)
            if buf is None:
                continue
            name = recipes.get(rid, f"recipe_{rid}")
            # Sanitize filename
            safe_name = "".join(c for c in name if c not in r'\/:*?"<>|')
            outer_zip.writestr(f"{safe_name}.zip", buf.read())

    outer_buf.seek(0)
    return StreamingResponse(
        outer_buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=recipes_export.zip"},
    )


@router.post("/recipes/import")
async def import_recipe_zip(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    """Import recipe(s) from a ZIP file. Supports single recipe ZIP or batch ZIP containing multiple recipe ZIPs."""
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be a .zip file")
    content = await file.read()

    imported_ids = []
    buf = io.BytesIO(content)
    try:
        zf = zipfile.ZipFile(buf, "r")
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file")

    with zf:
        names = zf.namelist()
        if "recipe.json" in names:
            # Single recipe ZIP
            try:
                recipe_id = await import_recipe(content, db)
                imported_ids.append(recipe_id)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")
        else:
            # Batch ZIP - each entry is a recipe ZIP
            zip_entries = [n for n in names if n.endswith(".zip")]
            if not zip_entries:
                raise HTTPException(status_code=400, detail="ZIP does not contain recipe.json or nested .zip files")
            for entry_name in zip_entries:
                try:
                    inner_content = zf.read(entry_name)
                    recipe_id = await import_recipe(inner_content, db)
                    imported_ids.append(recipe_id)
                except Exception:
                    continue  # Skip failed imports

    return {"recipe_ids": imported_ids, "count": len(imported_ids)}
