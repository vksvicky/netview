from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Interface

router = APIRouter()


@router.get("/{device_id}/{if_index}")
def get_interface_metrics(device_id: str, if_index: int, db: Session = Depends(get_db)) -> dict:
    iface = (
        db.query(Interface)
        .filter(Interface.device_id == device_id, Interface.if_index == if_index)
        .first()
    )
    if not iface:
        return {}
    return {
        "deviceId": device_id,
        "ifIndex": if_index,
        "lastCounters": iface.last_counters or {},
    }


