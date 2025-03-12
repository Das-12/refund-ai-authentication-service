from sqlalchemy.orm import Session
from .models import Role, Permission
from ..auth import User
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from .models import RoleRequest
from typing import List


def get_user_roles(user: User):
    return [role.name for role in user.roles]

def get_user_permissions(user: User):
    return [permission.name for role in user.roles for permission in role.permissions]

def has_permission(user: User, permission_name: str):
    for role in user.roles:
        # print(f"role is {role}")
        for permission in role.permissions:
            # print(f"permission is {permission}")
            if permission.name == permission_name:
                return True
    return False

def assign_role_to_user(db: Session, user: User, role_name: str):
    role = db.query(Role).filter(Role.name == role_name).first()
    if role and role not in user.roles:
        user.roles.append(role)
        db.commit()
        db.refresh(user)
    return user

def update_role(role_id: int, role_data: RoleRequest, db: Session):
    role = db.query(Role).filter(Role.id == role_id).first()
    if role is None:
        raise HTTPException(status_code=404, detail=f"role with id {role_id} is not found")
    
    if role_data.name is not None:
        role.name = role_data.name
    if role_data.description is not None:
        role.description = role_data.description
        
    db.add(role)
    db.commit()
    db.refresh(role)
    
    return True


def delete_role(role_id: int, db:Session):
    role = db.query(Role).filter(Role.id == role_id).first()
    if role is not None:
        if role.is_active != False:
            role.is_active = False
            db.commit()
            db.refresh(role)
            return True
        else:
            role.is_active = True
            db.commit()
            db.refresh(role)
            return True
    else:
        raise HTTPException(status_code=404, detail=f"role with id {role_id} is not found")
    
    

def assign_permission_to_role(db: Session, role_id: int, permission_ids: List[int]):
    role = db.query(Role).filter(Role.id == role_id).first()
    permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id'{role_id}' not found",
        )
        
    if not permissions or len(permissions) != len(permission_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"One or more permissions not found",
        )
    for permission in permissions:
        if permission not in role.permissions:
            role.permissions.append(permission)
    db.commit()
    db.refresh(role)
    return role

# def create_role(db: Session, role_name: str):
#     role = db.query(Role).filter(Role.name == role_name).first()
#     if not role:
#         role = Role(name=role_name)
#         db.add(role)
#         db.commit()
#         db.refresh(role)
#     return role