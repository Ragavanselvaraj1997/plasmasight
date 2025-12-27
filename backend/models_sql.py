from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role_id = Column(Integer, ForeignKey("roles.role_id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    role = relationship("Role", back_populates="users")

class Role(Base):
    __tablename__ = "roles"
    role_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True) # admin, engineer, internal, viewer
    
    users = relationship("User", back_populates="role")

class SensorMetadata(Base):
    __tablename__ = "sensor_metadata"
    sensor_id = Column(String, primary_key=True, index=True)
    type = Column(String) # pressure, gas_flow, RF_power
    location = Column(String) # chamber, port
    calibration_date = Column(DateTime)

class ModelMetadata(Base):
    __tablename__ = "model_metadata"
    model_version = Column(String, primary_key=True, index=True)
    name = Column(String) # ANN, BNN
    trained_on = Column(String) # data range
    mse_baseline = Column(Float)
    deployed_at = Column(DateTime)

class DeploymentHistory(Base):
    __tablename__ = "deployment_history"
    deployment_id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String, ForeignKey("model_metadata.model_version"))
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String) # canary, promoted, rolled-back

class ControlCommand(Base):
    __tablename__ = "control_commands"
    command_id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    delta_RF = Column(Float)
    delta_gas = Column(Float)
    source = Column(String) # auto/manual

class Alert(Base):
    __tablename__ = "alerts"
    alert_id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    module_name = Column(String)
    alert_type = Column(String)
    severity = Column(String)
    resolved = Column(Boolean, default=False)

# TimescaleDB Hypertable targets (modeled as regular PG tables for SQLAlchemy)
class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id = Column(Integer, primary_key=True, index=True) # In Timescale, would be part of composite PK with timestamp
    sensor_id = Column(String, ForeignKey("sensor_metadata.sensor_id"))
    timestamp = Column(DateTime, index=True)
    value = Column(Float)
    quality_flag = Column(Integer)

class ImageMetric(Base):
    __tablename__ = "image_metrics"
    image_id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True)
    mean_R = Column(Float)
    mean_G = Column(Float)
    mean_B = Column(Float)
    edge_density = Column(Float)

class InferenceLog(Base):
    __tablename__ = "inference_logs"
    inference_id = Column(String, primary_key=True, index=True)
    timestamp = Column(DateTime, index=True)
    model_version = Column(String, ForeignKey("model_metadata.model_version"))
    predicted_depth = Column(Float)
    uncertainty = Column(Float)
    latency_ms = Column(Float)
