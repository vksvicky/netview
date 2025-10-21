from fastapi import APIRouter
from typing import List

router = APIRouter()


@router.get("")
def list_alerts() -> List[dict]:
    return []


