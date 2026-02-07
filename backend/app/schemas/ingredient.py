from pydantic import BaseModel


class IngredientCategoryCreate(BaseModel):
    name: str


class IngredientCategoryOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


class IngredientCreate(BaseModel):
    name: str
    unit: str
    calorie: float | None = None
    category_id: int | None = None


class IngredientUpdate(BaseModel):
    name: str | None = None
    unit: str | None = None
    calorie: float | None = None
    category_id: int | None = None


class IngredientOut(BaseModel):
    id: int
    name: str
    unit: str
    calorie: float | None = None
    category_id: int | None = None
    category: str = ""

    model_config = {"from_attributes": True}
