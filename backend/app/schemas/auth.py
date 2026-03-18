from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


class UserProfile(BaseModel):
    id: uuid.UUID
    email: str
    first_name: Optional[str] = None
    last_name: str
    role: str
    is_active: bool
    tenant_id: Optional[uuid.UUID] = None
    icb_id: Optional[uuid.UUID] = None
    practice_ods_code: Optional[str] = None
    sub_icb_ods_code: Optional[str] = None
    org_level: Optional[str] = None
    org_ods_code: Optional[str] = None
    org_name: Optional[str] = None

    model_config = {"from_attributes": True}
