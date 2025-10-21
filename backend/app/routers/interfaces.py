from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Interface

router = APIRouter()


@router.get("")
def list_interfaces(db: Session = Depends(get_db)) -> List[dict]:
    ifaces = db.query(Interface).all()
    return [
        {
            "id": i.id,
            "deviceId": i.device_id,
            "ifIndex": i.if_index,
            "name": i.name,
            "speed": i.speed,
            "mac": i.mac,
            "adminStatus": i.admin_status,
            "operStatus": i.oper_status,
        }
        for i in ifaces
    ]


@router.get("/{device_id}")
def list_interfaces_for_device(device_id: str, db: Session = Depends(get_db)) -> List[dict]:
    ifaces = db.query(Interface).filter(Interface.device_id == device_id).all()
    return [
        {
            "id": i.id,
            "deviceId": i.device_id,
            "ifIndex": i.if_index,
            "name": i.name,
            "speed": i.speed,
            "mac": i.mac,
            "adminStatus": i.admin_status,
            "operStatus": i.oper_status,
        }
        for i in ifaces
    ]


@router.get("/{device_id}/{if_index}")
def get_interface(device_id: str, if_index: int, db: Session = Depends(get_db)) -> dict:
    i = (
        db.query(Interface)
        .filter(Interface.device_id == device_id, Interface.if_index == if_index)
        .first()
    )
    if not i:
        return {}
    return {
        "id": i.id,
        "deviceId": i.device_id,
        "ifIndex": i.if_index,
        "name": i.name,
        "speed": i.speed,
        "mac": i.mac,
        "adminStatus": i.admin_status,
        "operStatus": i.oper_status,
        "lastCounters": i.last_counters or {},
    }


