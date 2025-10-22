from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


DATABASE_URL = "sqlite:///./netview.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Device(Base):
    __tablename__ = "devices"
    id = Column(String, primary_key=True)
    hostname = Column(String, index=True)
    mgmt_ip = Column(String, index=True)
    vendor = Column(String)
    model = Column(String)
    roles = Column(JSON, default=list)
    status = Column(String, default="unknown")
    last_seen = Column(DateTime, default=datetime.utcnow)
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
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


