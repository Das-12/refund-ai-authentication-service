from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Table, Boolean
from ..database import Base
from pydantic import BaseModel
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List

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
    is_active = Column(Boolean, default=True)
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    
    def __str__(self):
        return f"Role(name={self.name})"
    
class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)
    description = Column(String(255))
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
    
    def __str__(self):
        return f"Permission(name={self.name})"

class RoleRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class AssignRoleRequest(BaseModel):
    username: str
    role_name: str

class AssignPermissionRequest(BaseModel):
    role_id: int
    permission_id: Optional[List[int]] = None