from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.auth import verify_token
from app.models.models import Ingredient, RecipeIngredient, IngredientCategory
from app.schemas.ingredient import (
    IngredientCreate, IngredientUpdate, IngredientOut,
    IngredientCategoryCreate, IngredientCategoryOut,
)

router = APIRouter(prefix="/api/ingredients", tags=["ingredients"])

# Color palette for auto-assignment
INGREDIENT_CATEGORY_COLORS = [
    "#2e86ab",  # blue
    "#a0522d",  # sienna
    "#5b7a5e",  # sage green
    "#6b5b95",  # purple
    "#d4726a",  # coral
    "#b8860b",  # goldenrod
    "#3d7068",  # teal
    "#c45d3e",  # warm red
    "#708090",  # slate
    "#8b6914",  # khaki
    "#c44569",  # rose
    "#3c6382",  # steel blue
]


async def _pick_ingredient_color(db: AsyncSession) -> str:
    """Pick next color from palette based on existing category count."""
    count = await db.scalar(select(func.count()).select_from(IngredientCategory))
    return INGREDIENT_CATEGORY_COLORS[(count or 0) % len(INGREDIENT_CATEGORY_COLORS)]


def _build_ingredient_out(ing: Ingredient) -> dict:
    """Build ingredient output with resolved category name."""
    return {
        "id": ing.id,
        "name": ing.name,
        "unit": ing.unit,
        "calorie": ing.calorie,
        "category_id": ing.category_id,
        "category": ing.category_rel.name if ing.category_rel else "",
    }


# ============== Ingredient Categories ==============

@router.get("/categories", response_model=list[IngredientCategoryOut])
async def list_ingredient_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(IngredientCategory).order_by(IngredientCategory.id))
    cats = result.scalars().all()
    # Auto-assign colors to categories that don't have one
    changed = False
    for idx, cat in enumerate(cats):
        if not cat.color:
            cat.color = INGREDIENT_CATEGORY_COLORS[idx % len(INGREDIENT_CATEGORY_COLORS)]
            changed = True
    if changed:
        await db.commit()
    return cats


@router.post("/categories", response_model=IngredientCategoryOut, status_code=status.HTTP_201_CREATED)
async def create_ingredient_category(
    data: IngredientCategoryCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    color = await _pick_ingredient_color(db)
    cat = IngredientCategory(name=data.name, color=color)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.delete("/categories/{cat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ingredient_category(
    cat_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    cat = await db.get(IngredientCategory, cat_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Ingredient category not found")
    # Check if category is referenced by ingredients
    ref_count = await db.scalar(
        select(func.count()).where(Ingredient.category_id == cat_id)
    )
    if ref_count and ref_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Category is used by {ref_count} ingredient(s), cannot delete",
        )
    await db.delete(cat)
    await db.commit()


# ============== Ingredients ==============

@router.get("", response_model=list[IngredientOut])
async def list_ingredients(
    q: str = Query("", description="Search keyword"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Ingredient).options(selectinload(Ingredient.category_rel)).order_by(Ingredient.name)
    if q:
        stmt = stmt.where(Ingredient.name.ilike(f"%{q}%"))
    result = await db.execute(stmt)
    return [_build_ingredient_out(i) for i in result.scalars().all()]


@router.post("", response_model=IngredientOut, status_code=status.HTTP_201_CREATED)
async def create_ingredient(data: IngredientCreate, db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    ing = Ingredient(name=data.name, unit=data.unit, calorie=data.calorie, category_id=data.category_id)
    db.add(ing)
    await db.commit()
    # Reload with category relationship
    result = await db.execute(
        select(Ingredient).where(Ingredient.id == ing.id).options(selectinload(Ingredient.category_rel))
    )
    ing = result.scalars().first()
    return _build_ingredient_out(ing)


@router.put("/{ingredient_id}", response_model=IngredientOut)
async def update_ingredient(
    ingredient_id: int,
    data: IngredientUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    ing = await db.get(Ingredient, ingredient_id)
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    if data.name is not None:
        ing.name = data.name
    if data.unit is not None:
        ing.unit = data.unit
    if data.calorie is not None:
        ing.calorie = data.calorie
    if data.category_id is not None:
        ing.category_id = data.category_id
    await db.commit()
    # Reload with category relationship
    result = await db.execute(
        select(Ingredient).where(Ingredient.id == ingredient_id).options(selectinload(Ingredient.category_rel))
    )
    ing = result.scalars().first()
    return _build_ingredient_out(ing)


@router.delete("/{ingredient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ingredient(
    ingredient_id: int,
    db: AsyncSession = Depends(get_db),
    _=Depends(verify_token),
):
    ing = await db.get(Ingredient, ingredient_id)
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    # Check if ingredient is referenced by recipes
    ref_count = await db.scalar(
        select(func.count()).where(RecipeIngredient.ingredient_id == ingredient_id)
    )
    if ref_count and ref_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Ingredient is used by {ref_count} recipe(s), cannot delete",
        )
    await db.delete(ing)
    await db.commit()
