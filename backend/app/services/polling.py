from typing import Dict, Any, List
from sqlalchemy.orm import Session
from ..models import Interface
from .snmp import SnmpClient
from ..metrics import (
    if_in_octets,
    if_out_octets,
    if_in_errors,
    if_out_errors,
    if_in_discards,
    if_out_discards,
)


class PollingService:
    def __init__(self, snmp_client: SnmpClient):
        self.snmp_client = snmp_client

    async def poll_device_interfaces(self, db: Session, device_id: str) -> None:
        counters: List[Dict[str, Any]] = await self.snmp_client.poll_interface_counters(device_id)
        for c in counters:
            if_index = str(c.get("ifIndex"))
            in_oct = c.get("inOctets", 0)
            out_oct = c.get("outOctets", 0)
            in_err = c.get("inErrors", 0)
            out_err = c.get("outErrors", 0)
            in_dis = c.get("inDiscards", 0)
            out_dis = c.get("outDiscards", 0)

            if_in_octets.labels(device_id=device_id, if_index=if_index).set(in_oct)
            if_out_octets.labels(device_id=device_id, if_index=if_index).set(out_oct)
            if_in_errors.labels(device_id=device_id, if_index=if_index).set(in_err)
            if_out_errors.labels(device_id=device_id, if_index=if_index).set(out_err)
            if_in_discards.labels(device_id=device_id, if_index=if_index).set(in_dis)
            if_out_discards.labels(device_id=device_id, if_index=if_index).set(out_dis)

            # Persist last counters
            iface = (
                db.query(Interface)
                .filter(Interface.device_id == device_id, Interface.if_index == int(if_index))
                .first()
            )
            if iface:
                iface.last_counters = {
                    "inOctets": in_oct,
                    "outOctets": out_oct,
                    "inErrors": in_err,
                    "outErrors": out_err,
                    "inDiscards": in_dis,
                    "outDiscards": out_dis,
                }
                db.add(iface)
        db.commit()


