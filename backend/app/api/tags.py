from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.auth import verify_token
from app.models.models import Tag, RecipeTag, TagCategory
from app.schemas.tag import TagCreate, TagUpdate, TagOut, TagCategoryCreate, TagCategoryOut

router = APIRouter(prefix="/api/tags", tags=["tags"])


# ============== Tag Categories ==============

@router.get("/categories", response_model=list[TagCategoryOut])
async def list_tag_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TagCategory).order_by(TagCategory.id))
    return result.scalars().all()


@router.post("/categories", response_model=TagCategoryOut, status_code=status.HTTP_201_CREATED)
async def create_tag_category(data: TagCategoryCreate, db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    cat = TagCategory(name=data.name)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return cat


@router.delete("/categories/{cat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag_category(cat_id: int, db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    cat = await db.get(TagCategory, cat_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Tag category not found")
    # Check if category is referenced by any tags
    ref_count = await db.scalar(select(func.count()).where(Tag.category_id == cat_id))
    if ref_count and ref_count > 0:
        raise HTTPException(status_code=409, detail=f"Category is used by {ref_count} tag(s), cannot delete")
    await db.delete(cat)
    await db.commit()


# ============== Tags ==============

@router.get("", response_model=list[TagOut])
async def list_tags(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Tag).options(selectinload(Tag.category_rel)).order_by(Tag.category_id, Tag.name)
    )
    tags = result.scalars().all()
    return [
        TagOut(
            id=t.id,
            name=t.name,
            category_id=t.category_id,
            category=t.category_rel.name if t.category_rel else "",
        )
        for t in tags
    ]


@router.post("", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def create_tag(data: TagCreate, db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    tag = Tag(name=data.name, category_id=data.category_id)
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    # Eagerly load category
    result = await db.execute(
        select(Tag).where(Tag.id == tag.id).options(selectinload(Tag.category_rel))
    )
    tag = result.scalars().first()
    return TagOut(
        id=tag.id,
        name=tag.name,
        category_id=tag.category_id,
        category=tag.category_rel.name if tag.category_rel else "",
    )


@router.put("/{tag_id}", response_model=TagOut)
async def update_tag(tag_id: int, data: TagUpdate, db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    tag = await db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    if data.name is not None:
        tag.name = data.name
    if data.category_id is not None:
        tag.category_id = data.category_id
    await db.commit()
    # Eagerly load category
    result = await db.execute(
        select(Tag).where(Tag.id == tag_id).options(selectinload(Tag.category_rel))
    )
    tag = result.scalars().first()
    return TagOut(
        id=tag.id,
        name=tag.name,
        category_id=tag.category_id,
        category=tag.category_rel.name if tag.category_rel else "",
    )


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_db), _=Depends(verify_token)):
    tag = await db.get(Tag, tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    # Check if tag is referenced by recipes
    ref_count = await db.scalar(select(func.count()).where(RecipeTag.tag_id == tag_id))
    if ref_count and ref_count > 0:
        raise HTTPException(status_code=409, detail=f"Tag is used by {ref_count} recipe(s), cannot delete")
    await db.delete(tag)
    await db.commit()
