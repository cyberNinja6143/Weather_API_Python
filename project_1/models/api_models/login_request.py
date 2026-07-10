"""Request model for the login endpoint."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="Registered username.")
    password: str = Field(..., min_length=1, description="Plaintext password.")
