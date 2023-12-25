from datetime import datetime

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class MyBaseModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: datetime = Field(default=datetime.utcnow())
    updated_at: datetime = Field(default=datetime.utcnow())

    class Config:
        allow_population_by_field_name = True
        # to handle the id field as a string
        json_encoders = {ObjectId: str}
