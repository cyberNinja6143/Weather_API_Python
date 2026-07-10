"""Request model for the registration endpoint."""

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=128, description="Desired username.")
    password: str = Field(..., min_length=6, description="Plaintext password (min 6 characters).")
