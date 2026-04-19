from pydantic import BaseModel
from enum import Enum

class UserRole(str, Enum):
    user  = "user"
    admin = "admin"

class InternalUser(BaseModel):
    id:   int
    role: UserRole

class UserValidate(BaseModel):
    id:        int
    role:      UserRole
    is_active: bool

    model_config = {"from_attributes": True}