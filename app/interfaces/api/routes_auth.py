from fastapi import APIRouter, Depends, HTTPException

from app.application.auth_use_cases import AuthUseCases
from app.domain.errors import InvalidCredentials
from app.interfaces.api.dependencies import get_auth_use_cases
from app.interfaces.api.schemas import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, auth: AuthUseCases = Depends(get_auth_use_cases)) -> TokenResponse:
    try:
        token = auth.login(payload.username, payload.password)
    except InvalidCredentials:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=token)

