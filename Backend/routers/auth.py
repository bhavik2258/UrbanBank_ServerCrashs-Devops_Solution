from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from auth import authenticate_user, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict[str, str]


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    user = authenticate_user(str(request.email), request.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    from auth import JWT_EXPIRE_MINUTES

    return LoginResponse(
        access_token=create_access_token(user),
        expires_in=JWT_EXPIRE_MINUTES * 60,
        user=user,
    )
