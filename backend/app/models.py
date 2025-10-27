from datetime import datetime, UTC
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, create_engine, Boolean, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


DATABASE_URL = "sqlite:///./netview.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def utc_now():
    """Return current UTC datetime"""
    return datetime.now(UTC)


class Device(Base):
    __tablename__ = "devices"
    id = Column(String, primary_key=True)
    hostname = Column(String, index=True)
    mgmt_ip = Column(String, index=True)
    vendor = Column(String)
    model = Column(String)
    roles = Column(JSON, default=list)
    status = Column(String, default="unknown")
    last_seen = Column(DateTime, default=utc_now)
    connection_type = Column(String, default="Unknown")
    ip_version = Column(String, default="IPv4")
    device_name = Column(String)
    interfaces = relationship("Interface", back_populates="device")


class Interface(Base):
    __tablename__ = "interfaces"
    id = Column(String, primary_key=True)
    device_id = Column(String, ForeignKey("devices.id"), index=True)
    if_index = Column(Integer, index=True)
    name = Column(String)
    speed = Column(Integer)
    mac = Column(String)
    admin_status = Column(String)
    oper_status = Column(String)
    last_counters = Column(JSON, default=dict)
    device = relationship("Device", back_populates="interfaces")


class Edge(Base):
    __tablename__ = "edges"
    id = Column(String, primary_key=True)
    src_device_id = Column(String, index=True)
    src_if_index = Column(Integer)
    dst_device_id = Column(String, index=True)
    dst_if_index = Column(Integer)
    link_type = Column(String)
    vlan_tags = Column(JSON, default=list)
    confidence = Column(Integer, default=100)


class UserSettings(Base):
    __tablename__ = "user_settings"
    id = Column(String, primary_key=True)  # MAC address or IP address
    device_type = Column(String)  # 'mac_mapping' or 'ip_mapping'
    vendor = Column(String)
    model = Column(String)
    hostname = Column(String)
    notes = Column(String)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class DeviceHistory(Base):
    __tablename__ = "device_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String, ForeignKey("devices.id"), index=True)
    event_type = Column(String, index=True)  # 'online', 'offline', 'ip_change', 'status_change'
    previous_status = Column(String)
    new_status = Column(String)
    previous_ip = Column(String)
    new_ip = Column(String)
    event_timestamp = Column(DateTime, default=utc_now, index=True)
    duration_seconds = Column(Integer)  # Duration of previous session (for offline events)
    event_metadata = Column(JSON, default=dict)  # Additional event data (renamed from metadata)
    device = relationship("Device")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, autoincrement=True)
    notification_type = Column(String, index=True)  # 'new_device', 'device_offline', 'device_online', 'ip_change', 'topology_change', 'security_alert'
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    device_id = Column(String, ForeignKey("devices.id"), index=True)
    severity = Column(String, default="info")  # 'info', 'warning', 'error', 'critical'
    is_read = Column(Boolean, default=False, index=True)
    is_acknowledged = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, default=utc_now, index=True)
    acknowledged_at = Column(DateTime)
    acknowledged_by = Column(String)  # User who acknowledged
    notification_data = Column(JSON, default=dict)  # Additional notification metadata
    device = relationship("Device")


class NotificationRule(Base):
    __tablename__ = "notification_rules"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    notification_type = Column(String, index=True)  # Type of event to monitor
    conditions = Column(JSON, default=dict)  # Conditions for triggering (e.g., vendor, status, IP range)
    is_enabled = Column(Boolean, default=True, index=True)
    severity = Column(String, default="info")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


def init_db():
    Base.metadata.create_all(bind=engine)