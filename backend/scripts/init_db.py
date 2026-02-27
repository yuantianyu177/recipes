#!/usr/bin/env python3
"""
Initialize database with test data.

This script will:
1. Drop all existing tables and recreate schema
2. Create tag categories, tags, ingredient categories, and ingredients
3. Create 10 sample recipes with images
4. Sync MeiliSearch index

Usage:
  cd backend && source venv/bin/activate
  python scripts/init_db.py
"""
import asyncio
import sys
import os
import uuid
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.core.database import Base
from app.models.models import (
    TagCategory, Tag, IngredientCategory, Ingredient,
    Recipe, RecipeIngredient, RecipeImage,
)


# =====================================================
# Data from design template (temp-designs/design-a-magazine.html)
# =====================================================

TAG_CATEGORIES = {
    "菜系": "#c45d3e",
    "场景": "#b8860b",
    "烹饪方式": "#6b5b95",
}

TAGS = [
    ("家常菜", "菜系"), ("川菜", "菜系"), ("粤菜", "菜系"), ("淮扬菜", "菜系"),
    ("海鲜", "场景"), ("甜品", "场景"), ("汤羹", "场景"),
    ("素食", "场景"), ("快手菜", "场景"),
    ("烘焙", "烹饪方式"),
]

INGREDIENT_CATEGORIES = {
    "主料": "#2e86ab",
    "辅料": "#a0522d",
    "调料": "#5b7a5e",
    "酱料": "#d4726a",
}

# (name, unit, calorie_per_unit, category)
INGREDIENTS = [
    # Main
    ("猪五花肉", "克", 3.95, "主料"),
    ("小白菜", "棵", 8.0, "主料"),
    ("鸡蛋", "个", 78.0, "主料"),
    ("嫩豆腐", "块", 62.0, "主料"),
    ("肉末", "克", 2.10, "主料"),
    ("鲈鱼", "条", 280.0, "主料"),
    ("猪排骨", "克", 2.78, "主料"),
    ("抹茶粉", "克", 3.24, "主料"),
    ("马斯卡彭", "克", 4.29, "主料"),
    ("手指饼干", "根", 20.0, "主料"),
    ("牛腩", "克", 3.32, "主料"),
    ("西红柿", "个", 22.0, "主料"),
    ("土豆", "个", 77.0, "主料"),
    ("黄瓜", "根", 16.0, "主料"),
    ("鸡胸肉", "克", 1.33, "主料"),
    ("大虾", "只", 35.0, "主料"),
    ("粉丝", "把", 170.0, "主料"),
    ("藕", "节", 70.0, "主料"),
    ("糯米", "克", 3.48, "主料"),
    # Side
    ("葱", "根", 5.0, "辅料"),
    ("姜", "片", 2.0, "辅料"),
    ("蒜", "瓣", 4.0, "辅料"),
    ("芝麻", "克", 5.59, "辅料"),
    ("花生", "克", 5.67, "辅料"),
    # Seasonings
    ("盐", "勺", 0.0, "调料"),
    ("糖", "勺", 16.0, "调料"),
    ("冰糖", "粒", 5.0, "调料"),
    ("红糖", "勺", 15.0, "调料"),
    ("生抽", "勺", 8.0, "调料"),
    ("老抽", "勺", 10.0, "调料"),
    ("蚝油", "勺", 9.0, "调料"),
    ("醋", "勺", 2.0, "调料"),
    ("香醋", "勺", 2.5, "调料"),
    ("料酒", "勺", 10.0, "调料"),
    ("花椒", "克", 2.58, "调料"),
    ("花椒粉", "克", 2.58, "调料"),
    ("八角", "个", 4.0, "调料"),
    ("干辣椒", "个", 3.0, "调料"),
    ("淀粉", "勺", 30.0, "调料"),
    ("食用油", "勺", 90.0, "调料"),
    ("芝麻油", "勺", 89.0, "调料"),
    ("番茄酱", "勺", 15.0, "调料"),
    ("桂花蜜", "勺", 25.0, "调料"),
    # Sauces
    ("豆瓣酱", "勺", 12.0, "酱料"),
    ("蒸鱼豉油", "勺", 8.0, "酱料"),
]

RECIPES = [
    {
        "name": "红烧狮子头",
        "description": "经典淮扬名菜，肥瘦相间的肉糜搓成大丸子，先炸后炖，汤汁浓郁鲜美。配上嫩绿的青菜心，色香味俱全，是宴客的压轴硬菜。",
        "steps": "<ol><li>猪五花肉剁成肉糜，加入葱姜水、盐、生抽、鸡蛋搅拌上劲</li><li>搓成大丸子，入油锅炸至表面金黄</li><li>砂锅中放入小白菜垫底，放入炸好的狮子头</li><li>加入高汤、生抽、老抽、料酒，大火烧开转小火炖1小时</li><li>炖至汤汁浓稠，肉丸酥烂即可</li></ol>",
        "tips": "肉糜要搅拌上劲才能成型。炖煮时间要足够，小火慢炖才能入味。",
        "tags": ["家常菜", "淮扬菜"],
        "ingredients": [
            ("猪五花肉", "500"), ("小白菜", "2"), ("姜", "5"), ("葱", "2"),
            ("鸡蛋", "1"), ("生抽", "2"), ("老抽", "1"), ("料酒", "2"),
            ("盐", "1"), ("食用油", "3"),
        ],
        "image_seed": "featured", "image_size": "900/600",
    },
    {
        "name": "麻婆豆腐",
        "description": "麻辣鲜香，嫩滑的豆腐裹满红亮的酱汁，花椒的麻与辣椒的辣完美交融，一口下去满嘴留香。",
        "steps": "<ol><li>豆腐切小块，用开水焯一下捞出沥干</li><li>猪肉剁成肉末</li><li>锅中倒油，放入花椒、干辣椒煸香</li><li>加入肉末炒散变色</li><li>放入豆瓣酱炒出红油</li><li>加入生抽、老抽调味</li><li>放入豆腐轻轻翻炒，加少许水焖煮2分钟</li><li>水淀粉勾芡，撒上葱花和花椒粉即可</li></ol>",
        "tips": "豆腐焯水可以去豆腥味且不易碎。花椒要用小火慢慢煸出香味。",
        "tags": ["川菜"],
        "ingredients": [
            ("嫩豆腐", "1"), ("肉末", "100"), ("葱", "2"), ("姜", "3"), ("蒜", "3"),
            ("花椒", "5"), ("花椒粉", "2"), ("干辣椒", "5"), ("豆瓣酱", "2"),
            ("生抽", "2"), ("老抽", "0.5"), ("淀粉", "1"), ("食用油", "3"), ("盐", "0.5"),
        ],
        "image_seed": "recipe1", "image_size": "600/750",
    },
    {
        "name": "清蒸鲈鱼",
        "description": "鲜嫩的鲈鱼只需简单清蒸，淋上滚烫的葱姜丝热油，鲜美至极。",
        "steps": "<ol><li>鲈鱼处理干净，两面划几刀方便入味</li><li>鱼身抹少许盐和料酒，放上姜片腌制10分钟</li><li>大火蒸8-10分钟至鱼肉熟透</li><li>倒掉蒸出的汤汁，铺上葱丝和姜丝</li><li>淋上蒸鱼豉油，浇上滚烫的热油即可</li></ol>",
        "tips": "蒸鱼时间不宜过长，8-10分钟即可。蒸好后一定要倒掉腥味汤汁。",
        "tags": ["粤菜", "海鲜"],
        "ingredients": [
            ("鲈鱼", "1"), ("葱", "3"), ("姜", "5"),
            ("蒸鱼豉油", "2"), ("料酒", "1"), ("盐", "0.5"), ("食用油", "2"),
        ],
        "image_seed": "recipe2", "image_size": "600/500",
    },
    {
        "name": "糖醋排骨",
        "description": "酸甜适口的经典家常菜，排骨外酥里嫩，裹着晶莹剔透的糖醋汁，每一口都是童年的味道。撒上白芝麻点缀，色泽诱人。",
        "steps": "<ol><li>排骨洗净切段，冷水下锅焯水去血沫</li><li>锅中倒油，放入排骨煎至两面金黄</li><li>加入姜片、葱段翻炒</li><li>调入生抽、老抽、醋、冰糖、番茄酱和适量水</li><li>大火烧开转中小火焖煮20分钟</li><li>大火收汁至浓稠，撒上芝麻即可</li></ol>",
        "tips": "排骨焯水后要沥干水分再煎，这样更容易上色。糖醋比例可根据口味调整。",
        "tags": ["家常菜"],
        "ingredients": [
            ("猪排骨", "500"), ("姜", "3"), ("葱", "2"),
            ("醋", "3"), ("冰糖", "8"), ("番茄酱", "2"),
            ("生抽", "2"), ("老抽", "1"), ("芝麻", "3"), ("食用油", "2"),
        ],
        "image_seed": "recipe3", "image_size": "600/850",
    },
    {
        "name": "抹茶提拉米苏",
        "description": "日式与意式的完美碰撞，浓郁的马斯卡彭奶酪搭配清新抹茶，层层叠叠的口感令人沉醉。",
        "steps": "<ol><li>将抹茶粉用少量热水化开，放凉备用</li><li>马斯卡彭奶酪加糖打发至顺滑</li><li>手指饼干快速蘸取抹茶液，铺在容器底部</li><li>铺上一层马斯卡彭奶酪糊</li><li>重复铺层，最后撒上抹茶粉</li><li>冷藏4小时以上，让风味融合</li></ol>",
        "tips": "手指饼干蘸抹茶液要快，不要泡太久否则会软烂。冷藏时间越长风味越好。",
        "tags": ["烘焙", "甜品"],
        "ingredients": [
            ("抹茶粉", "15"), ("马斯卡彭", "250"), ("手指饼干", "12"),
            ("糖", "3"), ("鸡蛋", "2"),
        ],
        "image_seed": "recipe4", "image_size": "600/550",
    },
    {
        "name": "番茄牛腩煲",
        "description": "番茄的酸甜与牛腩的醇厚在砂锅中慢炖三小时，汤色红亮，肉质酥烂入味。冬日里的一碗暖心之作，配上热腾腾的白米饭，幸福感满溢。",
        "steps": "<ol><li>牛腩切块，冷水下锅焯水去血沫，捞出洗净</li><li>西红柿切块，土豆去皮切块</li><li>锅中倒油，放入姜片、八角炒香</li><li>加入牛腩翻炒，倒入料酒去腥</li><li>加入西红柿翻炒出汁</li><li>转入砂锅，加入开水没过食材</li><li>大火烧开转小火炖2小时</li><li>加入土豆继续炖30分钟，调入盐即可</li></ol>",
        "tips": "牛腩要炖足够时间才能软烂。番茄要炒出汁水，汤色才会红亮。",
        "tags": ["家常菜", "汤羹"],
        "ingredients": [
            ("牛腩", "500"), ("西红柿", "3"), ("土豆", "2"),
            ("姜", "5"), ("八角", "2"), ("料酒", "2"),
            ("盐", "1"), ("食用油", "2"),
        ],
        "image_seed": "recipe5", "image_size": "600/700",
    },
    {
        "name": "凉拌黄瓜",
        "description": "爽脆开胃的夏日小菜，拍碎的黄瓜拌上蒜末和香醋，五分钟搞定。",
        "steps": "<ol><li>黄瓜洗净，用刀拍碎后切段</li><li>蒜切末</li><li>将黄瓜放入碗中，加入蒜末</li><li>调入香醋、生抽、盐、芝麻油拌匀</li><li>可根据口味加入小米辣</li></ol>",
        "tips": "黄瓜拍碎比切的更容易入味。拌好后立即食用口感最佳。",
        "tags": ["素食", "快手菜"],
        "ingredients": [
            ("黄瓜", "2"), ("蒜", "4"), ("香醋", "2"),
            ("生抽", "1"), ("盐", "0.5"), ("芝麻油", "1"),
        ],
        "image_seed": "recipe6", "image_size": "600/480",
    },
    {
        "name": "宫保鸡丁",
        "description": "鸡丁滑嫩，花生酥脆，干辣椒的香气与宫保汁的甜咸完美平衡。经典川菜的代表之作，百吃不厌。",
        "steps": "<ol><li>鸡胸肉切丁，加入料酒、盐、淀粉腌制15分钟</li><li>花生炒熟备用，干辣椒剪段</li><li>调制宫保汁：醋、生抽、糖、淀粉、水混合</li><li>锅中倒油烧热，放入鸡丁滑炒至变色盛出</li><li>锅中留底油，放入干辣椒、花椒炒香</li><li>倒回鸡丁，淋入宫保汁翻炒均匀</li><li>加入花生翻炒几下即可出锅</li></ol>",
        "tips": "鸡丁腌制后更嫩滑。花生最后放入，保持酥脆口感。",
        "tags": ["川菜"],
        "ingredients": [
            ("鸡胸肉", "300"), ("花生", "30"), ("干辣椒", "8"),
            ("花椒", "3"), ("醋", "2"), ("生抽", "2"), ("糖", "1"),
            ("料酒", "1"), ("淀粉", "1"), ("盐", "0.5"), ("食用油", "3"),
        ],
        "image_seed": "recipe7", "image_size": "600/900",
    },
    {
        "name": "蒜蓉粉丝蒸虾",
        "description": "鲜虾铺在粉丝上，浇上蒜蓉酱汁入锅蒸制，粉丝吸满虾的鲜味。",
        "steps": "<ol><li>粉丝提前用温水泡软，铺在盘底</li><li>大虾开背去虾线，铺在粉丝上</li><li>蒜切末，用油炒至金黄</li><li>蒜蓉加入生抽、蚝油、糖调成酱汁</li><li>将酱汁浇在虾上</li><li>大火蒸8分钟即可，出锅撒上葱花</li></ol>",
        "tips": "虾开背后更容易入味。蒜蓉要炒至金黄才香。",
        "tags": ["海鲜", "粤菜"],
        "ingredients": [
            ("大虾", "12"), ("粉丝", "1"), ("蒜", "8"),
            ("生抽", "2"), ("蚝油", "1"), ("糖", "0.5"),
            ("葱", "2"), ("食用油", "2"),
        ],
        "image_seed": "recipe8", "image_size": "600/600",
    },
    {
        "name": "桂花糯米藕",
        "description": "莲藕塞入糯米慢煮数小时，淋上桂花蜜，软糯香甜，是江南的经典甜品。",
        "steps": "<ol><li>糯米提前浸泡4小时</li><li>莲藕去皮，切去一端作为盖子</li><li>将泡好的糯米塞入藕孔中，用牙签固定盖子</li><li>放入锅中，加入红糖、冰糖和水</li><li>大火烧开转小火煮2-3小时</li><li>取出切片，淋上桂花蜜即可</li></ol>",
        "tips": "糯米要塞紧实，煮的时间要足够长才能软糯。",
        "tags": ["甜品", "素食"],
        "ingredients": [
            ("藕", "2"), ("糯米", "150"), ("桂花蜜", "3"),
            ("红糖", "3"), ("冰糖", "5"),
        ],
        "image_seed": "recipe9", "image_size": "600/780",
    },
]


# =====================================================
# Database operations
# =====================================================

async def main():
    engine = create_async_engine(settings.DATABASE_URL)

    # Drop all tables and recreate
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] Database tables dropped and recreated.")

    # Resolve upload directory - also copy to Docker volume if running on host
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    os.makedirs(upload_dir, exist_ok=True)
    for f in os.listdir(upload_dir):
        fp = os.path.join(upload_dir, f)
        if os.path.isfile(fp):
            os.unlink(fp)

    # Check if backend runs in Docker container
    import shutil
    docker_bin = shutil.which("docker")
    container_name = "recipe-backend-dev"
    use_docker_cp = False
    if docker_bin:
        ret = os.popen(f"docker inspect {container_name} --format '{{{{.State.Running}}}}' 2>/dev/null").read().strip()
        if ret == "true":
            use_docker_cp = True
            os.popen(f'docker exec {container_name} sh -c "rm -f /app/uploads/*.jpg /app/uploads/*.png /app/uploads/*.webp"').read()

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as db:
        # Tag categories
        tag_cats = {}
        for name, color in TAG_CATEGORIES.items():
            db.add(TagCategory(name=name, color=color))
        await db.flush()
        for c in (await db.execute(select(TagCategory))).scalars().all():
            tag_cats[c.name] = c.id

        # Tags
        tags = {}
        for name, cat_name in TAGS:
            db.add(Tag(name=name, category_id=tag_cats[cat_name]))
        await db.flush()
        for t in (await db.execute(select(Tag))).scalars().all():
            tags[t.name] = t

        # Ingredient categories
        ing_cats = {}
        for name, color in INGREDIENT_CATEGORIES.items():
            db.add(IngredientCategory(name=name, color=color))
        await db.flush()
        for c in (await db.execute(select(IngredientCategory))).scalars().all():
            ing_cats[c.name] = c.id

        # Ingredients
        ings = {}
        for name, unit, cal, cat_name in INGREDIENTS:
            db.add(Ingredient(name=name, unit=unit, calorie=cal, category_id=ing_cats[cat_name]))
        await db.flush()
        for i in (await db.execute(select(Ingredient))).scalars().all():
            ings[i.name] = i

        # Recipes + images
        img_count = 0
        for r_data in RECIPES:
            recipe = Recipe(
                name=r_data["name"],
                description=r_data["description"],
                steps=r_data["steps"],
                tips=r_data["tips"],
            )
            for tag_name in r_data["tags"]:
                recipe.tags.append(tags[tag_name])
            db.add(recipe)
            await db.flush()
            for ing_name, amount in r_data["ingredients"]:
                db.add(RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=ings[ing_name].id,
                    amount=amount,
                ))

            # Download cover image from picsum.photos
            seed = r_data["image_seed"]
            size = r_data["image_size"]
            try:
                url = f"https://picsum.photos/seed/{seed}/{size}"
                resp = requests.get(url, allow_redirects=True, timeout=30)
                resp.raise_for_status()
                filename = f"{uuid.uuid4().hex}.jpg"
                filepath = os.path.join(upload_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(resp.content)
                db.add(RecipeImage(
                    recipe_id=recipe.id,
                    image_path=f"/uploads/{filename}",
                    sort_order=0,
                ))
                # Copy to Docker volume if needed
                if use_docker_cp:
                    os.popen(f"docker cp {filepath} {container_name}:/app/uploads/").read()
                img_count += 1
                print(f"  [IMG] {r_data['name']} -> {filename}")
            except Exception as e:
                print(f"  [WARN] Failed to download image for {r_data['name']}: {e}")

        await db.commit()
        print(f"[OK] Data inserted:")
        print(f"     Tag categories:        {len(TAG_CATEGORIES)}")
        print(f"     Tags:                  {len(TAGS)}")
        print(f"     Ingredient categories: {len(INGREDIENT_CATEGORIES)}")
        print(f"     Ingredients:           {len(INGREDIENTS)}")
        print(f"     Recipes:               {len(RECIPES)}")
        print(f"     Images:                {img_count}")

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

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
