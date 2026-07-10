"""Response model for a successful JWT login."""

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token.")
    token_type: str = Field(default="bearer", description="Token type, always 'bearer'.")
    expires_in: int = Field(..., description="Seconds until the token expires (30 days = 2_592_000).")
