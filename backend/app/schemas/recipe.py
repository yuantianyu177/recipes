from pydantic import BaseModel


class RecipeImageOut(BaseModel):
    id: int
    image_path: str
    sort_order: int

    model_config = {"from_attributes": True}


class RecipeIngredientIn(BaseModel):
    ingredient_id: int
    amount: str = ""


class RecipeIngredientOut(BaseModel):
    id: int
    ingredient_id: int
    amount: str
    category_id: int | None = None
    category: str = ""
    ingredient_name: str = ""
    ingredient_unit: str = ""
    ingredient_calorie: float | None = None

    model_config = {"from_attributes": True}


class RecipeCreate(BaseModel):
    name: str
    description: str = ""
    steps: str = ""
    tips: str = ""
    tag_ids: list[int] = []
    ingredients: list[RecipeIngredientIn] = []


class RecipeUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    steps: str | None = None
    tips: str | None = None
    tag_ids: list[int] | None = None
    ingredients: list[RecipeIngredientIn] | None = None


class RecipeOut(BaseModel):
    id: int
    name: str
    description: str
    steps: str
    tips: str
    created_at: str | None = None
    updated_at: str | None = None
    images: list[RecipeImageOut] = []
    tags: list["TagBrief"] = []
    ingredients: list[RecipeIngredientOut] = []

    model_config = {"from_attributes": True}


class RecipeListOut(BaseModel):
    id: int
    name: str
    description: str
    calories: int = 0
    created_at: str | None = None
    updated_at: str | None = None
    images: list[RecipeImageOut] = []
    tags: list["TagBrief"] = []
    ingredients: list[RecipeIngredientOut] = []

    model_config = {"from_attributes": True}


class TagBrief(BaseModel):
    id: int
    name: str
    category: str = ""
    color: str | None = None

    model_config = {"from_attributes": True}
