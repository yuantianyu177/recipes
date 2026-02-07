import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.auth import verify_token
from app.models.models import Recipe, Tag, RecipeIngredient, Ingredient
from app.schemas.recipe import RecipeCreate, RecipeUpdate, RecipeOut, RecipeListOut
from app.services.search import index_recipe, remove_recipe

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


def _build_ingredient_out(ri: RecipeIngredient) -> dict:
    """Build ingredient output dict. Category comes from the ingredient itself."""
    ing = ri.ingredient
    cat_name = ""
    cat_id = None
    if ing and ing.category_rel:
        cat_name = ing.category_rel.name
        cat_id = ing.category_id
    elif ing:
        cat_id = ing.category_id
    return {
        "id": ri.id,
        "ingredient_id": ri.ingredient_id,
        "amount": ri.amount,
        "category_id": cat_id,
        "category": cat_name,
        "ingredient_name": ing.name if ing else "",
        "ingredient_unit": ing.unit if ing else "",
        "ingredient_calorie": ing.calorie if ing else None,
    }


def _sync_search_index(recipe, tag_names: list[str], main_ingredients: list[str]):
    """Sync recipe to MeiliSearch index. Best-effort, log errors."""
    try:
        index_recipe(recipe.id, recipe.name, tag_names, main_ingredients)
    except Exception as e:
        logger.warning(f"Failed to sync search index for recipe {recipe.id}: {e}")


def _format_datetime(dt):
    """Format datetime to ISO string for JSON output."""
    if dt is None:
        return None
    return dt.isoformat()


def _calc_calories(recipe) -> int:
    """Calculate total calories for a recipe from its ingredients."""
    total = 0.0
    if hasattr(recipe, "recipe_ingredients"):
        for ri in recipe.recipe_ingredients:
            try:
                amount = float(ri.amount) if ri.amount else 0
            except (ValueError, TypeError):
                amount = 0
            cal = ri.ingredient.calorie if ri.ingredient and ri.ingredient.calorie else 0
            total += amount * cal
    return round(total)


async def _build_recipe_list_out(recipe) -> dict:
    """Build recipe list output dict."""
    return {
        "id": recipe.id,
        "name": recipe.name,
        "description": recipe.description or "",
        "calories": _calc_calories(recipe),
        "created_at": _format_datetime(recipe.created_at),
        "updated_at": _format_datetime(recipe.updated_at),
        "images": recipe.images,
        "tags": [_build_tag_brief(t) for t in recipe.tags],
    }


def _build_tag_brief(tag) -> dict:
    """Build tag brief dict, resolving category name from relationship."""
    return {
        "id": tag.id,
        "name": tag.name,
        "category": tag.category_rel.name if tag.category_rel else "",
    }


# Shared eager-load options for recipe ingredients with their category
_ingredient_load = (
    selectinload(Recipe.recipe_ingredients)
    .selectinload(RecipeIngredient.ingredient)
    .selectinload(Ingredient.category_rel)
)


@router.get("", response_model=list[RecipeListOut])
async def list_recipes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Recipe)
        .options(
            selectinload(Recipe.images),
            selectinload(Recipe.tags).selectinload(Tag.category_rel),
            selectinload(Recipe.recipe_ingredients)
            .selectinload(RecipeIngredient.ingredient),
        )
        .order_by(Recipe.id.desc())
    )
    recipes = result.scalars().unique().all()
    return [await _build_recipe_list_out(r) for r in recipes]


@router.get("/{recipe_id}", response_model=RecipeOut)
async def get_recipe(recipe_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(
            selectinload(Recipe.images),
            selectinload(Recipe.tags).selectinload(Tag.category_rel),
            _ingredient_load,
        )
    )
    recipe = result.scalars().unique().first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    return {
        "id": recipe.id,
        "name": recipe.name,
        "description": recipe.description or "",
        "steps": recipe.steps or "",
        "tips": recipe.tips or "",
        "created_at": _format_datetime(recipe.created_at),
        "updated_at": _format_datetime(recipe.updated_at),
        "images": recipe.images,
        "tags": [_build_tag_brief(t) for t in recipe.tags],
        "ingredients": [_build_ingredient_out(ri) for ri in recipe.recipe_ingredients],
    }


@router.post("", response_model=RecipeOut, status_code=status.HTTP_201_CREATED)
async def create_recipe(data: RecipeCreate, db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    recipe = Recipe(
        name=data.name,
        description=data.description,
        steps=data.steps,
        tips=data.tips,
    )
    # Associate tags
    tag_names = []
    if data.tag_ids:
        tags = (await db.execute(
            select(Tag).where(Tag.id.in_(data.tag_ids)).options(selectinload(Tag.category_rel))
        )).scalars().all()
        recipe.tags = list(tags)
        tag_names = [t.name for t in tags]
    db.add(recipe)
    await db.flush()
    # Associate ingredients
    for item in data.ingredients:
        ri = RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=item.ingredient_id,
            amount=item.amount,
        )
        db.add(ri)
    await db.commit()
    # Reload for search indexing
    result = await db.execute(
        select(Recipe)
        .where(Recipe.id == recipe.id)
        .options(_ingredient_load)
    )
    recipe_full = result.scalars().unique().first()
    main_ingredients = []
    if recipe_full:
        main_cat_names = {"主料", "辅料"}
        main_ingredients = [
            ri.ingredient.name for ri in recipe_full.recipe_ingredients
            if ri.ingredient and ri.ingredient.category_rel
            and ri.ingredient.category_rel.name in main_cat_names
        ]
    _sync_search_index(recipe, tag_names, main_ingredients)
    return await get_recipe(recipe.id, db)


@router.put("/{recipe_id}", response_model=RecipeOut)
async def update_recipe(
    recipe_id: int,
    data: RecipeUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    # Eagerly load tags to avoid lazy-load MissingGreenlet error in async
    result = await db.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(selectinload(Recipe.tags))
    )
    recipe = result.scalars().unique().first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    if data.name is not None:
        recipe.name = data.name
    if data.description is not None:
        recipe.description = data.description
    if data.steps is not None:
        recipe.steps = data.steps
    if data.tips is not None:
        recipe.tips = data.tips
    # Update tags
    if data.tag_ids is not None:
        tags = (await db.execute(
            select(Tag).where(Tag.id.in_(data.tag_ids)).options(selectinload(Tag.category_rel))
        )).scalars().all()
        recipe.tags = list(tags)
    # Update ingredients
    if data.ingredients is not None:
        existing = await db.execute(
            select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id)
        )
        for ri in existing.scalars().all():
            await db.delete(ri)
        await db.flush()
        for item in data.ingredients:
            ri = RecipeIngredient(
                recipe_id=recipe_id,
                ingredient_id=item.ingredient_id,
                amount=item.amount,
            )
            db.add(ri)
    await db.commit()
    # Reload for search indexing
    result = await db.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(
            selectinload(Recipe.tags).selectinload(Tag.category_rel),
            _ingredient_load,
        )
    )
    recipe_full = result.scalars().unique().first()
    if recipe_full:
        tag_names = [t.name for t in recipe_full.tags]
        main_cat_names = {"主料", "辅料"}
        main_ingredients = [
            ri.ingredient.name for ri in recipe_full.recipe_ingredients
            if ri.ingredient and ri.ingredient.category_rel
            and ri.ingredient.category_rel.name in main_cat_names
        ]
        _sync_search_index(recipe_full, tag_names, main_ingredients)
    return await get_recipe(recipe_id, db)


@router.delete("/{recipe_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_recipe(recipe_id: int, db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    recipe = await db.get(Recipe, recipe_id)
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    await db.delete(recipe)
    await db.commit()
    try:
        remove_recipe(recipe_id)
    except Exception as e:
        logger.warning(f"Failed to remove recipe {recipe_id} from search index: {e}")
