from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.models import Recipe, RecipeIngredient

router = APIRouter(prefix="/api/share", tags=["share"])


@router.get("/{recipe_id}")
async def get_share_info(recipe_id: int, db: AsyncSession = Depends(get_db)):
    """Get recipe info for sharing (title, description, URL)."""
    result = await db.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(selectinload(Recipe.tags))
    )
    recipe = result.scalars().unique().first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")

    tag_names = [t.name for t in recipe.tags]

    return {
        "id": recipe.id,
        "name": recipe.name,
        "description": recipe.description[:200] if recipe.description else "",
        "tags": tag_names,
        "share_text": f"来看看这道菜：{recipe.name}",
    }
