"""Routes under /auth — register, login, and token issuance."""

from fastapi import APIRouter

from controllers.auth_controller import login, register

router = APIRouter(prefix="/auth", tags=["Authentication"])

router.add_api_route("/register", register, methods=["POST"])
router.add_api_route("/login", login, methods=["POST"], response_model=None)
