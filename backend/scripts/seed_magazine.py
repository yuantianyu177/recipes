#!/usr/bin/env python3
"""
Seed script: create recipes matching the design-a-magazine.html mockup.
Clears existing data first, then creates tags, ingredients, and 8 recipes
with images downloaded from picsum.photos.
"""
import requests
import time
import os
import tempfile

BASE = "http://localhost:8000/api"

# Login
resp = requests.post(f"{BASE}/auth/login", json={"username": "admin", "password": "admin123"})
resp.raise_for_status()
TOKEN = resp.json()["access_token"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def auth_headers():
    return {"Authorization": f"Bearer {TOKEN}"}

# ============ Step 1: Delete all existing recipes ============
print("Deleting all existing recipes...")
recipes = requests.get(f"{BASE}/recipes").json()
for r in recipes:
    requests.delete(f"{BASE}/recipes/{r['id']}", headers=HEADERS)
print(f"  Deleted {len(recipes)} recipes")

# Delete all existing tags
print("Deleting all existing tags...")
tags = requests.get(f"{BASE}/tags").json()
for t in tags:
    requests.delete(f"{BASE}/tags/{t['id']}", headers=HEADERS)
print(f"  Deleted {len(tags)} tags")

# Delete all existing ingredients
print("Deleting all existing ingredients...")
ingredients = requests.get(f"{BASE}/ingredients").json()
for i in ingredients:
    requests.delete(f"{BASE}/ingredients/{i['id']}", headers=HEADERS)
print(f"  Deleted {len(ingredients)} ingredients")

# Delete tag categories
print("Deleting tag categories...")
tag_cats = requests.get(f"{BASE}/tags/categories").json()
for c in tag_cats:
    requests.delete(f"{BASE}/tags/categories/{c['id']}", headers=HEADERS)
print(f"  Deleted {len(tag_cats)} tag categories")

# Delete ingredient categories
print("Deleting ingredient categories...")
ing_cats = requests.get(f"{BASE}/ingredients/categories").json()
for c in ing_cats:
    requests.delete(f"{BASE}/ingredients/categories/{c['id']}", headers=HEADERS)
print(f"  Deleted {len(ing_cats)} ingredient categories")

# ============ Step 2: Create tag categories ============
print("\nCreating tag categories...")
tag_category_names = ["菜系", "类型", "场景"]
tag_cat_map = {}
for name in tag_category_names:
    resp = requests.post(f"{BASE}/tags/categories", json={"name": name}, headers=HEADERS)
    resp.raise_for_status()
    cat = resp.json()
    tag_cat_map[name] = cat["id"]
    print(f"  Created tag category: {name} (id={cat['id']})")

# ============ Step 3: Create tags ============
print("\nCreating tags...")
tag_defs = [
    ("家常菜", "类型"), ("川菜", "菜系"), ("粤菜", "菜系"),
    ("淮扬菜", "菜系"), ("烘焙", "类型"), ("素食", "类型"),
    ("汤羹", "类型"), ("快手菜", "场景"), ("甜品", "类型"),
    ("海鲜", "类型"),
]
tag_map = {}
for tag_name, cat_name in tag_defs:
    resp = requests.post(f"{BASE}/tags", json={
        "name": tag_name,
        "category_id": tag_cat_map[cat_name]
    }, headers=HEADERS)
    resp.raise_for_status()
    tag = resp.json()
    tag_map[tag_name] = tag["id"]
    print(f"  Created tag: {tag_name} (id={tag['id']})")

# ============ Step 4: Create ingredient categories ============
print("\nCreating ingredient categories...")
ing_category_names = ["主料", "辅料", "调料"]
ing_cat_map = {}
for name in ing_category_names:
    resp = requests.post(f"{BASE}/ingredients/categories", json={"name": name}, headers=HEADERS)
    resp.raise_for_status()
    cat = resp.json()
    ing_cat_map[name] = cat["id"]
    print(f"  Created ingredient category: {name} (id={cat['id']})")

# ============ Step 5: Create ingredients ============
print("\nCreating ingredients...")
ingredient_defs = [
    # (name, unit, calorie_per_unit, category)
    ("猪肉", "克", 2.5, "主料"),
    ("青菜", "克", 0.2, "辅料"),
    ("生姜", "克", 0.5, "辅料"),
    ("料酒", "毫升", 0.9, "调料"),
    ("豆腐", "克", 0.8, "主料"),
    ("牛肉末", "克", 2.5, "主料"),
    ("花椒", "克", 2.0, "调料"),
    ("鲈鱼", "克", 1.1, "主料"),
    ("葱姜", "克", 0.3, "辅料"),
    ("蒸鱼豉油", "毫升", 0.7, "调料"),
    ("排骨", "克", 2.6, "主料"),
    ("白醋", "毫升", 0.2, "调料"),
    ("冰糖", "克", 4.0, "调料"),
    ("番茄酱", "克", 1.0, "调料"),
    ("抹茶粉", "克", 3.0, "主料"),
    ("马斯卡彭", "克", 4.0, "主料"),
    ("手指饼干", "克", 4.5, "主料"),
    ("牛腩", "克", 2.0, "主料"),
    ("番茄", "克", 0.2, "主料"),
    ("土豆", "克", 0.8, "辅料"),
    ("八角", "克", 3.0, "调料"),
    ("黄瓜", "克", 0.15, "主料"),
    ("大蒜", "克", 1.5, "辅料"),
    ("香醋", "毫升", 0.3, "调料"),
    ("鸡胸肉", "克", 1.7, "主料"),
    ("花生", "克", 5.7, "辅料"),
    ("干辣椒", "克", 3.0, "调料"),
]
ing_map = {}
for name, unit, cal, cat in ingredient_defs:
    resp = requests.post(f"{BASE}/ingredients", json={
        "name": name,
        "unit": unit,
        "calorie": cal,
        "category_id": ing_cat_map[cat]
    }, headers=HEADERS)
    resp.raise_for_status()
    ing = resp.json()
    ing_map[name] = ing["id"]
    print(f"  Created ingredient: {name} (id={ing['id']})")

# ============ Step 6: Create recipes ============
print("\nCreating recipes...")

recipe_defs = [
    {
        "name": "红烧狮子头",
        "description": "经典淮扬名菜，肥瘦相间的肉糜搓成大丸子，先炸后炖，汤汁浓郁鲜美。配上嫩绿的青菜心，色香味俱全，是宴客的压轴硬菜。",
        "steps": "1. 猪肉剁成肉糜，加入葱姜水、盐、料酒搅拌上劲\n2. 搓成大丸子，入油锅炸至金黄\n3. 砂锅中放入高汤，加入狮子头\n4. 小火慢炖1.5小时\n5. 加入青菜心，调味出锅",
        "tips": "肉糜要搅拌上劲才能成型，炸的时候油温不要太高",
        "tags": ["家常菜", "淮扬菜"],
        "ingredients": [("猪肉", "500"), ("青菜", "200"), ("生姜", "20"), ("料酒", "30")],
        "image_seed": "featured",
        "image_size": "900/600",
    },
    {
        "name": "麻婆豆腐",
        "description": "麻辣鲜香，嫩滑的豆腐裹满红亮的酱汁，花椒的麻与辣椒的辣完美交融，一口下去满嘴留香。",
        "steps": "1. 豆腐切块，焯水备用\n2. 牛肉末炒散\n3. 加入豆瓣酱、辣椒面炒出红油\n4. 加入豆腐和高汤，小火煮5分钟\n5. 勾芡，撒花椒粉出锅",
        "tips": "豆腐先焯水可以去豆腥味，也更不容易碎",
        "tags": ["川菜"],
        "ingredients": [("豆腐", "400"), ("牛肉末", "100"), ("花椒", "5")],
        "image_seed": "recipe1",
        "image_size": "600/750",
    },
    {
        "name": "清蒸鲈鱼",
        "description": "鲜嫩的鲈鱼只需简单清蒸，淋上滚烫的葱姜丝热油，鲜美至极。",
        "steps": "1. 鲈鱼处理干净，两面划刀\n2. 放入葱姜，大火蒸8分钟\n3. 倒掉蒸出的汤汁\n4. 铺上葱丝姜丝\n5. 淋上热油和蒸鱼豉油",
        "tips": "蒸鱼时间不要太长，8分钟刚好",
        "tags": ["粤菜", "海鲜"],
        "ingredients": [("鲈鱼", "500"), ("葱姜", "30"), ("蒸鱼豉油", "20")],
        "image_seed": "recipe2",
        "image_size": "600/500",
    },
    {
        "name": "糖醋排骨",
        "description": "酸甜适口的经典家常菜，排骨外酥里嫩，裹着晶莹剔透的糖醋汁，每一口都是童年的味道。撒上白芝麻点缀，色泽诱人。",
        "steps": "1. 排骨焯水去血沫\n2. 加入料酒、生抽腌制30分钟\n3. 裹上薄薄的淀粉，炸至金黄\n4. 锅中放入白醋、冰糖、番茄酱熬成糖醋汁\n5. 倒入排骨翻炒均匀，撒白芝麻",
        "tips": "炸排骨可以复炸一次更酥脆",
        "tags": ["家常菜"],
        "ingredients": [("排骨", "500"), ("白醋", "30"), ("冰糖", "40"), ("番茄酱", "20")],
        "image_seed": "recipe3",
        "image_size": "600/850",
    },
    {
        "name": "抹茶提拉米苏",
        "description": "日式与意式的完美碰撞，浓郁的马斯卡彭奶酪搭配清新抹茶，层层叠叠的口感令人沉醉。",
        "steps": "1. 蛋黄加糖打发，加入马斯卡彭拌匀\n2. 蛋白打发，轻轻拌入奶酪糊\n3. 抹茶粉加热水调成抹茶液\n4. 手指饼干蘸抹茶液，铺一层\n5. 铺一层奶酪糊，重复两次\n6. 冷藏4小时以上，撒抹茶粉装饰",
        "tips": "马斯卡彭要提前回温，拌的时候动作要轻",
        "tags": ["烘焙", "甜品"],
        "ingredients": [("抹茶粉", "15"), ("马斯卡彭", "250"), ("手指饼干", "100")],
        "image_seed": "recipe4",
        "image_size": "600/550",
    },
    {
        "name": "番茄牛腩煲",
        "description": "番茄的酸甜与牛腩的醇厚在砂锅中慢炖三小时，汤色红亮，肉质酥烂入味。冬日里的一碗暖心之作，配上热腾腾的白米饭，幸福感满溢。",
        "steps": "1. 牛腩切块焯水\n2. 番茄切块，土豆切块\n3. 锅中炒香八角、姜片\n4. 加入牛腩翻炒，倒入番茄\n5. 加水没过食材，大火烧开转小火\n6. 炖2-3小时至牛腩酥烂\n7. 加入土豆再炖30分钟",
        "tips": "番茄要炒出汁，牛腩要炖够时间才能酥烂",
        "tags": ["家常菜", "汤羹"],
        "ingredients": [("牛腩", "500"), ("番茄", "300"), ("土豆", "200"), ("八角", "3")],
        "image_seed": "recipe5",
        "image_size": "600/700",
    },
    {
        "name": "凉拌黄瓜",
        "description": "爽脆开胃的夏日小菜，拍碎的黄瓜拌上蒜末和香醋，五分钟搞定。",
        "steps": "1. 黄瓜洗净，用刀拍碎切段\n2. 大蒜切末\n3. 加入盐、香醋、生抽、香油\n4. 拌匀即可",
        "tips": "黄瓜要拍碎而不是切，这样更入味",
        "tags": ["素食", "快手菜"],
        "ingredients": [("黄瓜", "300"), ("大蒜", "10"), ("香醋", "15")],
        "image_seed": "recipe6",
        "image_size": "600/480",
    },
    {
        "name": "宫保鸡丁",
        "description": "鸡丁滑嫩，花生酥脆，干辣椒的香气与宫保汁的甜咸完美平衡。经典川菜的代表之作，百吃不厌。",
        "steps": "1. 鸡胸肉切丁，加料酒、淀粉腌制\n2. 花生炸至酥脆\n3. 锅中爆香干辣椒和花椒\n4. 加入鸡丁滑炒至变色\n5. 倒入宫保汁（醋、糖、酱油、淀粉水）\n6. 加入花生翻炒均匀",
        "tips": "鸡丁要滑油而不是炒，这样更嫩",
        "tags": ["川菜"],
        "ingredients": [("鸡胸肉", "300"), ("花生", "50"), ("干辣椒", "10")],
        "image_seed": "recipe7",
        "image_size": "600/900",
    },
]

def download_image(seed, size):
    """Download image from picsum.photos"""
    url = f"https://picsum.photos/seed/{seed}/{size}"
    resp = requests.get(url, allow_redirects=True, timeout=30)
    resp.raise_for_status()
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    tmp.write(resp.content)
    tmp.close()
    return tmp.name

for rdef in recipe_defs:
    # Create recipe
    resp = requests.post(f"{BASE}/recipes", json={
        "name": rdef["name"],
        "description": rdef["description"],
        "steps": rdef["steps"],
        "tips": rdef["tips"],
        "tag_ids": [tag_map[t] for t in rdef["tags"]],
        "ingredients": [
            {"ingredient_id": ing_map[name], "amount": amount}
            for name, amount in rdef["ingredients"]
        ],
    }, headers=HEADERS)
    resp.raise_for_status()
    recipe = resp.json()
    recipe_id = recipe["id"]
    print(f"  Created recipe: {rdef['name']} (id={recipe_id})")

    # Download and upload image
    try:
        print(f"    Downloading image (seed={rdef['image_seed']})...")
        img_path = download_image(rdef["image_seed"], rdef["image_size"])
        with open(img_path, "rb") as f:
            resp = requests.post(
                f"{BASE}/recipes/{recipe_id}/images",
                headers=auth_headers(),
                files={"file": ("cover.jpg", f, "image/jpeg")},
            )
            resp.raise_for_status()
            print(f"    Uploaded image: {resp.json()['image_path']}")
        os.unlink(img_path)
    except Exception as e:
        print(f"    Warning: Failed to download/upload image: {e}")

print("\nDone! All 8 recipes created successfully.")
