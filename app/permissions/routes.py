from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from .permissions import assign_permission_to_role,get_user_roles,assign_role_to_user,has_permission, get_user_permissions
from .models import AssignPermissionRequest, AssignRoleRequest, RoleRequest, Role, Permission
from ..database import get_db
from ..auth import decode_access_token, get_user

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Roles

@router.post("/roles")
async def create_role(role: RoleRequest, token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    user = get_user(db, username=decode_access_token(token))
    if not has_permission(user, "create_role"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    role = Role(name=role.name, description=role.description)
    db.add(role)
    db.commit()
    db.refresh(role)
    return role

@router.get("/roles")
async def list_roles(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = get_user(db, username=decode_access_token(token))
    if not has_permission(user, "view_roles"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    roles = db.query(Role).all()
    return roles

@router.post("/assign-role")
async def assign_role(roleRequest:AssignRoleRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    requesting_user = get_user(db, username=decode_access_token(token))
    if not has_permission(requesting_user, "assign_role"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    user = get_user(db, username=roleRequest.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user = assign_role_to_user(db, user, roleRequest.role_name)
    return {"username": user.username, "roles": get_user_roles(user)}

@router.get("/get-user-role-token")
async def list_roles_for_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    
    username = decode_access_token(token)
    
    user = get_user(db, username=username)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"username": user.username, "roles": get_user_roles(user)}

@router.get("/roles/{user_name}")
async def list_roles_for_user(user_name:str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    request_username = decode_access_token(token)
    request_user = get_user(db, username=request_username)
    if request_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid Token",
        )

    if not has_permission(request_user, "view_roles_of_user"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    user = get_user(db, username=user_name)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Username not found",
        )

    return {"username": user_name, "roles": get_user_roles(user)}



# Permissions

@router.post("/permissions")
async def create_permission(permission:RoleRequest, token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    user = get_user(db, username=decode_access_token(token))
    if not has_permission(user, "create_permission"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    permission = Permission(name=permission.name, description=permission.description)
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission

@router.get("/permissions")
async def list_permissions(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = get_user(db, username=decode_access_token(token))
    if not has_permission(user, "view_permissions"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    permissions = db.query(Permission).all()
    return permissions

@router.post("/assign-permission")
async def assign_permission(assignPermissionRequest:AssignPermissionRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    requesting_user = get_user(db, username=decode_access_token(token))
    if not has_permission(requesting_user, "assign_permissions"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    role = assign_permission_to_role(db, assignPermissionRequest.role_name, assignPermissionRequest.permission_name)
    return {"role": role.name, "permissions": [permission.name for permission in role.permissions]}

@router.get("/get-user-permission-token")
async def list_permissions_for_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):

    username = decode_access_token(token)

    user = get_user(db, username=username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"username": user.username, "permissions": get_user_permissions(user)}

@router.get("/permissions/{user_name}")
async def list_permissions_for_user(user_name:str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    
    request_username = decode_access_token(token)
    request_user = get_user(db, username=request_username)
    
    if request_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid Token",
        )

    if not has_permission(request_user, "view_roles_of_user"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    user = get_user(db, username=user_name)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Username not found",
        )

    return {"username": user_name, "permissions": get_user_permissions(user)}

@router.get("/cause-error")
async def cause_error():
    raise Exception("This is a test error from /cause-error")