from sqlalchemy import Column, String, ForeignKey, UUID
from sqlalchemy.orm import relationship
import uuid
from db_init import Base

class Block(Base):
    __tablename__ = "block"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)

class Config(Base):
    __tablename__ = "config"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    key = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)

class Credential(Base):
    __tablename__ = "credential"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

class Site(Base):
    __tablename__ = "site"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)

class Device(Base):
    __tablename__ = "device"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    site_id = Column(UUID, ForeignKey("site.id"), nullable=False)
    name = Column(String, nullable=False)
    site = relationship("Site")

class Interface(Base):
    __tablename__ = "interface"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID, ForeignKey("device.id"), nullable=False)
    name = Column(String, nullable=False)
    device = relationship("Device")

class Circuit(Base):
    __tablename__ = "circuit"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)

class Tag(Base):
    __tablename__ = "tag"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)

class TagAssignment(Base):
    __tablename__ = "tag_assignment"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    tag_id = Column(UUID, ForeignKey("tag.id"), nullable=False)
    entity_id = Column(UUID, nullable=False)  # Generic ID for any tagged entity
    entity_type = Column(String, nullable=False)  # E.g., 'device', 'interface'
