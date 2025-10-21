from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from .config import settings


security = HTTPBasic()


def basic_auth(credentials: HTTPBasicCredentials = Depends(security)):
    if not settings.basic_auth_enabled:
        return
    correct_user = settings.basic_auth_username
    correct_pass = settings.basic_auth_password
    if credentials.username != correct_user or credentials.password != correct_pass:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


