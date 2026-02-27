from pydantic import BaseModel


class TagCategoryCreate(BaseModel):
    name: str


class TagCategoryOut(BaseModel):
    id: int
    name: str
    color: str | None = None

    model_config = {"from_attributes": True}


class TagCreate(BaseModel):
    name: str
    category_id: int | None = None


class TagUpdate(BaseModel):
    name: str | None = None
    category_id: int | None = None


class TagOut(BaseModel):
    id: int
    name: str
    category_id: int | None = None
    category: str = ""
    color: str | None = None

    model_config = {"from_attributes": True}
