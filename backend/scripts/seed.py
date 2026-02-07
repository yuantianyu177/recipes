#!/usr/bin/env python3
"""
Seed the database with sample data for testing.

Usage:
  cd backend
  python3 scripts/seed.py          # Insert seed data only
  python3 scripts/seed.py --reset  # Drop all tables, recreate, then seed
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.core.database import Base
from app.models.models import (
    TagCategory, Tag, IngredientCategory, Ingredient,
    Recipe, RecipeIngredient,
)


async def reset_database():
    """Drop all tables and recreate them."""
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("[OK] Database tables dropped and recreated.")


async def seed_data():
    """Insert sample data into the database."""
    engine = create_async_engine(settings.DATABASE_URL)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        # ===== Tag Categories =====
        tag_cats_data = ["菜系", "口味", "场景", "烹饪方式", "难度"]
        tag_cats = {}
        for name in tag_cats_data:
            db.add(TagCategory(name=name))
        await db.flush()
        for c in (await db.execute(select(TagCategory))).scalars().all():
            tag_cats[c.name] = c.id

        # ===== Tags =====
        tags_data = [
            ("川菜", "菜系"), ("粤菜", "菜系"), ("湘菜", "菜系"),
            ("鲁菜", "菜系"), ("家常菜", "菜系"), ("西餐", "菜系"),
            ("麻辣", "口味"), ("酸甜", "口味"), ("咸鲜", "口味"),
            ("清淡", "口味"), ("香辣", "口味"),
            ("早餐", "场景"), ("午餐", "场景"), ("晚餐", "场景"),
            ("下饭菜", "场景"), ("快手菜", "场景"), ("宴客菜", "场景"),
            ("炒", "烹饪方式"), ("蒸", "烹饪方式"), ("煮", "烹饪方式"),
            ("烤", "烹饪方式"), ("炖", "烹饪方式"), ("凉拌", "烹饪方式"),
            ("简单", "难度"), ("中等", "难度"), ("困难", "难度"),
        ]
        tags = {}
        for name, cat_name in tags_data:
            db.add(Tag(name=name, category_id=tag_cats[cat_name]))
        await db.flush()
        for t in (await db.execute(select(Tag))).scalars().all():
            tags[t.name] = t

        # ===== Ingredient Categories =====
        ing_cats_data = ["主料", "辅料", "调料"]
        ing_cats = {}
        for name in ing_cats_data:
            db.add(IngredientCategory(name=name))
        await db.flush()
        for c in (await db.execute(select(IngredientCategory))).scalars().all():
            ing_cats[c.name] = c.id

        # ===== Ingredients =====
        ingredients_data = [
            ("西红柿", "个", 22.0, "主料"), ("鸡蛋", "个", 78.0, "主料"),
            ("土豆", "个", 77.0, "主料"), ("青椒", "个", 22.0, "主料"),
            ("猪肉", "克", 2.5, "主料"), ("鸡胸肉", "克", 1.67, "主料"),
            ("虾仁", "克", 0.93, "主料"), ("豆腐", "块", 76.0, "主料"),
            ("米饭", "碗", 232.0, "主料"), ("面条", "份", 280.0, "主料"),
            ("白菜", "棵", 15.0, "主料"), ("茄子", "个", 25.0, "主料"),
            ("黄瓜", "根", 16.0, "辅料"), ("胡萝卜", "根", 41.0, "辅料"),
            ("葱", "根", 5.0, "辅料"), ("姜", "片", 2.0, "辅料"),
            ("蒜", "瓣", 4.0, "辅料"), ("香菜", "棵", 3.0, "辅料"),
            ("盐", "勺", 0.0, "调料"), ("糖", "勺", 16.0, "调料"),
            ("酱油", "勺", 8.0, "调料"), ("醋", "勺", 2.0, "调料"),
            ("料酒", "勺", 10.0, "调料"), ("生抽", "勺", 8.0, "调料"),
            ("老抽", "勺", 10.0, "调料"), ("蚝油", "勺", 9.0, "调料"),
            ("花椒", "克", 2.6, "调料"), ("干辣椒", "个", 3.0, "调料"),
            ("淀粉", "勺", 30.0, "调料"), ("食用油", "勺", 90.0, "调料"),
        ]
        ings = {}
        for name, unit, cal, cat_name in ingredients_data:
            db.add(Ingredient(name=name, unit=unit, calorie=cal, category_id=ing_cats[cat_name]))
        await db.flush()
        for i in (await db.execute(select(Ingredient))).scalars().all():
            ings[i.name] = i

        # ===== Recipes =====
        recipes_data = [
            {
                "name": "西红柿炒鸡蛋",
                "description": "家常经典菜品，酸甜可口，营养丰富，是每个家庭餐桌上的常客。",
                "steps": "<ol><li>西红柿切块，鸡蛋打散加少许盐搅匀</li><li>锅中倒油烧热，倒入蛋液炒至凝固盛出</li><li>锅中再加少许油，放入西红柿翻炒出汁</li><li>加入糖、盐调味，倒回鸡蛋翻炒均匀即可</li></ol>",
                "tips": "西红柿要炒出汁水，鸡蛋不要炒太老。可以加少许糖提鲜。",
                "tags": ["家常菜", "酸甜", "快手菜", "炒", "简单"],
                "ingredients": [("西红柿", "2"), ("鸡蛋", "3"), ("葱", "1"), ("盐", "1"), ("糖", "0.5"), ("食用油", "2")],
            },
            {
                "name": "麻婆豆腐",
                "description": "四川经典名菜，麻辣鲜香，豆腐嫩滑入味。",
                "steps": "<ol><li>豆腐切小块，用开水焯一下捞出沥干</li><li>猪肉剁成肉末</li><li>锅中倒油，放入花椒、干辣椒煸香</li><li>加入肉末炒散变色</li><li>加入生抽、老抽、蚝油调味</li><li>放入豆腐轻轻翻炒，加少许水焖煮2分钟</li><li>水淀粉勾芡，撒上葱花即可</li></ol>",
                "tips": "豆腐焯水可以去豆腥味且不易碎。花椒要用小火慢慢煸出香味。",
                "tags": ["川菜", "麻辣", "下饭菜", "炒", "中等"],
                "ingredients": [("豆腐", "1"), ("猪肉", "100"), ("葱", "2"), ("姜", "3"), ("蒜", "3"), ("花椒", "5"), ("干辣椒", "5"), ("生抽", "2"), ("老抽", "0.5"), ("蚝油", "1"), ("淀粉", "1"), ("食用油", "3"), ("盐", "0.5")],
            },
            {
                "name": "清蒸虾仁",
                "description": "清淡鲜美的海鲜菜品，保留虾仁的原汁原味。",
                "steps": "<ol><li>虾仁洗净，用料酒、盐腌制10分钟</li><li>姜切丝，葱切段</li><li>虾仁摆盘，放上姜丝</li><li>大火蒸6-8分钟</li><li>出锅后淋上少许生抽，撒上葱花</li></ol>",
                "tips": "虾仁不要蒸太久，否则口感会变老。",
                "tags": ["粤菜", "清淡", "宴客菜", "蒸", "简单"],
                "ingredients": [("虾仁", "200"), ("葱", "2"), ("姜", "5"), ("料酒", "1"), ("生抽", "1"), ("盐", "0.5")],
            },
            {
                "name": "酸辣土豆丝",
                "description": "开胃下饭的经典家常菜，酸辣爽脆。",
                "steps": "<ol><li>土豆去皮切丝，泡入清水中去淀粉</li><li>青椒切丝，蒜切末</li><li>锅中倒油烧热，放入干辣椒、花椒爆香</li><li>放入土豆丝大火快炒</li><li>加入醋、盐、生抽调味</li><li>放入青椒丝翻炒几下即可出锅</li></ol>",
                "tips": "土豆丝要切细并泡水去淀粉，炒的时候大火快炒保持脆爽。",
                "tags": ["家常菜", "香辣", "下饭菜", "炒", "简单"],
                "ingredients": [("土豆", "2"), ("青椒", "1"), ("蒜", "3"), ("干辣椒", "3"), ("花椒", "2"), ("醋", "2"), ("盐", "1"), ("生抽", "1"), ("食用油", "2")],
            },
            {
                "name": "红烧肉",
                "description": "色泽红亮、肥而不腻的经典硬菜，入口即化。",
                "steps": "<ol><li>猪肉切块，冷水下锅焯水去血沫，捞出洗净</li><li>锅中放少许油，加糖小火炒出糖色</li><li>放入肉块翻炒上色</li><li>加入生抽、老抽、料酒</li><li>加入姜片、葱段和适量开水没过肉</li><li>大火烧开转小火炖1小时</li><li>大火收汁至浓稠即可</li></ol>",
                "tips": "炒糖色时要小火，糖色变琥珀色即可放肉。炖煮时间要足够才能软烂。",
                "tags": ["家常菜", "咸鲜", "宴客菜", "炖", "中等"],
                "ingredients": [("猪肉", "500"), ("葱", "2"), ("姜", "5"), ("糖", "3"), ("生抽", "3"), ("老抽", "1"), ("料酒", "2"), ("食用油", "1"), ("盐", "0.5")],
            },
            {
                "name": "凉拌黄瓜",
                "description": "清爽开胃的夏日凉菜，简单快手。",
                "steps": "<ol><li>黄瓜洗净，用刀拍碎切段</li><li>蒜切末，香菜切段</li><li>碗中加入生抽、醋、糖、盐、辣椒油拌匀</li><li>将调料汁浇在黄瓜上</li><li>撒上蒜末和香菜，拌匀即可</li></ol>",
                "tips": "黄瓜拍碎比切片更入味。拌好后可以冷藏10分钟口感更佳。",
                "tags": ["家常菜", "酸甜", "快手菜", "凉拌", "简单"],
                "ingredients": [("黄瓜", "2"), ("蒜", "3"), ("香菜", "2"), ("生抽", "2"), ("醋", "1"), ("糖", "0.5"), ("盐", "0.5")],
            },
        ]

        for r_data in recipes_data:
            recipe = Recipe(name=r_data["name"], description=r_data["description"], steps=r_data["steps"], tips=r_data["tips"])
            for tag_name in r_data["tags"]:
                recipe.tags.append(tags[tag_name])
            db.add(recipe)
            await db.flush()
            for ing_name, amount in r_data["ingredients"]:
                db.add(RecipeIngredient(recipe_id=recipe.id, ingredient_id=ings[ing_name].id, amount=amount))

        await db.commit()
        print(f"[OK] Seed data inserted:")
        print(f"     Tag categories: {len(tag_cats_data)}")
        print(f"     Tags:           {len(tags_data)}")
        print(f"     Ing categories: {len(ing_cats_data)}")
        print(f"     Ingredients:    {len(ingredients_data)}")
        print(f"     Recipes:        {len(recipes_data)}")

    await engine.dispose()

    # Sync MeiliSearch index
    try:
        from app.services.search import index_recipe, setup_index
        from sqlalchemy.orm import selectinload

        setup_index()
        print("[OK] MeiliSearch index configured.")

        engine2 = create_async_engine(settings.DATABASE_URL)
        sf2 = async_sessionmaker(engine2, class_=AsyncSession, expire_on_commit=False)
        async with sf2() as db2:
            result = await db2.execute(
                select(Recipe).options(
                    selectinload(Recipe.tags),
                    selectinload(Recipe.recipe_ingredients)
                    .selectinload(RecipeIngredient.ingredient)
                    .selectinload(Ingredient.category_rel),
                )
            )
            for r in result.scalars().unique().all():
                tag_names = [t.name for t in r.tags]
                main_ings = [
                    ri.ingredient.name for ri in r.recipe_ingredients
                    if ri.ingredient and ri.ingredient.category_rel
                    and ri.ingredient.category_rel.name in {"主料", "辅料"}
                ]
                index_recipe(r.id, r.name, tag_names, main_ings)
        await engine2.dispose()
        print("[OK] Search index synced.")
    except Exception as e:
        print(f"[WARN] Search index sync failed: {e}")


async def main():
    if "--reset" in sys.argv:
        await reset_database()
    await seed_data()
    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
