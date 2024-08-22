from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table
from ..database import Base
from pydantic import BaseModel
from sqlalchemy.orm import relationship
from datetime import datetime

# Association table for many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('role_id', Integer, ForeignKey('roles.id'))
)

# Association table for many-to-many relationship between roles and permissions
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id')),
    Column('permission_id', Integer, ForeignKey('permissions.id'))
)

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)
    description = Column(String(255))
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)
    description = Column(String(255))
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class RoleRequest(BaseModel):
    name: str
    description: str

class AssignRoleRequest(BaseModel):
    username: str
    role_name: str

class AssignPermissionRequest(BaseModel):
    role_name: str
    permission_name: str