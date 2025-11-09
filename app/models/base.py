from datetime import datetime, timezone
from typing import Annotated, Any

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, GetCoreSchemaHandler
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:

        def serialize_objectid(value, serializer, info):
            """
            Serialize ObjectId based on serialization mode.

            Args:
                value: The ObjectId to serialize
                serializer: Pydantic's serializer (not used here)
                info: SerializationInfo with mode ('json' or 'python')
            """
            if info.mode == "json":
                return str(value)  # Convert to string for JSON/API
            return value  # Keep as ObjectId for Python/DB

        return core_schema.union_schema(
            [
                # Accept ObjectId objects
                core_schema.is_instance_schema(ObjectId),
                # Accept valid ObjectId strings
                core_schema.chain_schema(
                    [
                        core_schema.str_schema(),
                        core_schema.no_info_plain_validator_function(cls.validate),
                    ]
                ),
            ],
            serialization=core_schema.wrap_serializer_function_ser_schema(
                serialize_objectid,
                info_arg=True,
            ),
        )

    @classmethod
    def validate(cls, v: Any) -> ObjectId:
        """Validate and convert input to ObjectId"""
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError(f"Invalid ObjectId: {v}")

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        """Define how this appears in OpenAPI/JSON schema"""
        return {
            "type": "string",
            "format": "objectid",
            "example": "507f1f77bcf86cd799439011",
        }

PydanticObjectId = Annotated[ObjectId, PyObjectId]


class MyBaseModel(BaseModel):
    id: PydanticObjectId = Field(
        default_factory=PyObjectId, alias="_id", description="MongoDB document ID"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), alias="createdAt"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), alias="updatedAt"
    )

    def update_timestamp(self):
        self.updated_at = datetime.now(timezone.utc)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        validate_assignment=True,
        from_attributes=True,
    )
