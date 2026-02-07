"""ZIP import/export service for recipes."""
import json
import os
import zipfile
import io
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.models import (
    Recipe, RecipeImage, RecipeIngredient, Tag, Ingredient,
    IngredientCategory,
)


async def export_recipe(recipe_id: int, db: AsyncSession) -> io.BytesIO:
    """Export a single recipe as a ZIP file containing recipe.json and images/."""
    result = await db.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(
            selectinload(Recipe.images),
            selectinload(Recipe.tags).selectinload(Tag.category_rel),
            selectinload(Recipe.recipe_ingredients)
            .selectinload(RecipeIngredient.ingredient)
            .selectinload(Ingredient.category_rel),
        )
    )
    recipe = result.scalars().unique().first()
    if not recipe:
        return None

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        image_entries = []
        for img in sorted(recipe.images, key=lambda x: x.sort_order):
            filename = os.path.basename(img.image_path)
            image_entries.append(f"images/{filename}")
            filepath = os.path.join(os.path.abspath(settings.UPLOAD_DIR), filename)
            if os.path.exists(filepath):
                zf.write(filepath, f"images/{filename}")

        ingredients_data = []
        for ri in recipe.recipe_ingredients:
            ing = ri.ingredient
            cat_name = ing.category_rel.name if ing and ing.category_rel else ""
            ingredients_data.append({
                "name": ing.name if ing else "",
                "amount": ri.amount,
                "category": cat_name,
            })

        recipe_data = {
            "version": "1.0",
            "recipe": {
                "name": recipe.name,
                "description": recipe.description or "",
                "steps": recipe.steps or "",
                "tips": recipe.tips or "",
                "images": image_entries,
                "ingredients": ingredients_data,
                "tags": [t.name for t in recipe.tags],
            }
        }
        zf.writestr("recipe.json", json.dumps(recipe_data, ensure_ascii=False, indent=2))

    buf.seek(0)
    return buf


async def _resolve_ingredient_category_id(db: AsyncSession, name: str) -> int | None:
    """Resolve ingredient category name to id, creating if needed."""
    if not name:
        return None
    result = await db.execute(select(IngredientCategory).where(IngredientCategory.name == name))
    cat = result.scalars().first()
    if cat:
        return cat.id
    cat = IngredientCategory(name=name)
    db.add(cat)
    await db.flush()
    return cat.id


async def import_recipe(zip_data: bytes, db: AsyncSession) -> int:
    """Import a recipe from a ZIP file. Returns the new recipe ID."""
    buf = io.BytesIO(zip_data)
    with zipfile.ZipFile(buf, "r") as zf:
        recipe_json = json.loads(zf.read("recipe.json"))
        recipe_info = recipe_json["recipe"]

        recipe = Recipe(
            name=recipe_info["name"],
            description=recipe_info.get("description", ""),
            steps=recipe_info.get("steps", ""),
            tips=recipe_info.get("tips", ""),
        )

        # Associate tags
        for tag_name in recipe_info.get("tags", []):
            existing = await db.execute(select(Tag).where(Tag.name == tag_name))
            tag = existing.scalars().first()
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                await db.flush()
            recipe.tags.append(tag)

        db.add(recipe)
        await db.flush()

        # Associate ingredients
        for ing_data in recipe_info.get("ingredients", []):
            existing = await db.execute(
                select(Ingredient).where(Ingredient.name == ing_data["name"])
            )
            ingredient = existing.scalars().first()
            if not ingredient:
                cat_id = await _resolve_ingredient_category_id(
                    db, ing_data.get("category", "")
                )
                ingredient = Ingredient(name=ing_data["name"], unit="份", category_id=cat_id)
                db.add(ingredient)
                await db.flush()
            ri = RecipeIngredient(
                recipe_id=recipe.id,
                ingredient_id=ingredient.id,
                amount=ing_data.get("amount", ""),
            )
            db.add(ri)

        # Extract images
        upload_dir = os.path.abspath(settings.UPLOAD_DIR)
        os.makedirs(upload_dir, exist_ok=True)
        sort_order = 0
        for image_path in recipe_info.get("images", []):
            try:
                image_data = zf.read(image_path)
                ext = os.path.splitext(image_path)[1] or ".jpg"
                filename = f"{uuid.uuid4().hex}{ext}"
                filepath = os.path.join(upload_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(image_data)
                image = RecipeImage(
                    recipe_id=recipe.id,
                    image_path=f"/uploads/{filename}",
                    sort_order=sort_order,
                )
                db.add(image)
                sort_order += 1
            except KeyError:
                pass

        await db.commit()
        return recipe.id
