from sqlalchemy.orm import Session
from .models import Role, Permission
from ..auth import User
from sqlalchemy.orm import Session
from fastapi import HTTPException, status


def get_user_roles(user: User):
    return [role.name for role in user.roles]

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


def assign_permission_to_role(db: Session, role_name: str, permission_name: str):
    role = db.query(Role).filter(Role.name == role_name).first()
    permission = db.query(Permission).filter(Permission.name == permission_name).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role '{role_name}' not found",
        )

    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Permission '{permission_name}' not found",
        )

    if permission not in role.permissions:
        role.permissions.append(permission)
        db.commit()
        db.refresh(role)
    return role
