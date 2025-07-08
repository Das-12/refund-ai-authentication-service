from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from .permissions import assign_permission_to_role,get_user_roles,assign_role_to_user,has_permission, get_user_permissions, update_role, delete_role
from .models import AssignPermissionRequest, AssignRoleRequest, RoleRequest, Role, Permission, RoleOut
from ..database import get_db
from ..auth import decode_access_token, get_user
import logging
from sqlalchemy.orm import joinedload

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Roles

@router.post("/roles")
async def create_role(role: RoleRequest, token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    try:
        user = get_user(db, username=decode_access_token(token))
        if not has_permission(user, "create_role"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        existing_role = db.query(Role).filter(Role.name == role.name).first()
        if existing_role:
            raise HTTPException(status_code=409, detail=f"Role with the name {role.name} already exists")
        else:
            role = Role(name=role.name, description=role.description)
            db.add(role)
            db.commit()
            db.refresh(role)
            return role
    except Exception as e:
        logging.error(f"Error creating role: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/roles")
async def list_roles(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = get_user(db, username=decode_access_token(token))
    if not has_permission(user, "view_roles"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    try:
        # print("roles try block started")
        # roles = db.query(Role).all()
        roles = db.query(Role).options(joinedload(Role.permissions)).filter(Role.is_active != False).all()
        return roles
    except Exception as e:
        # print("roles except block started")
        logging.error(f"Error listing roles: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/assign-role")
async def assign_role(roleRequest:AssignRoleRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
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
    except Exception as e:
        logging.error(f"Error assigning role: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/get-user-role-token")
async def list_roles_for_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
    
        username = decode_access_token(token)
        
        user = get_user(db, username=username)
        
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return {"username": user.username, "roles": get_user_roles(user)}
    except Exception as e:
        logging.error(f"Error getting user roles: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/roles/{user_name}")
async def list_roles_for_user(user_name:str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    print("list roles started in auth")
    try:
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
    
    except HTTPException as http_exc:
        # If an expected HTTPException occurs, re-raise it as is
        raise http_exc

    except Exception as e:
        # Log the actual error and return an internal server error response
        logging.error(f"Unexpected error getting user roles: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail={str(e)}  # Return the actual error message
        )
        
@router.get("/get_role_by_id/{role_id}")
async def get_role_by_id_endpoint(role_id: int, db: Session = Depends(get_db)):
    role = db.query(Role).options(joinedload(Role.permissions)).filter(Role.id == role_id).first()
    return role

@router.put("/update_role/{role_id}", response_model=dict)
async def update_role_auth_endpoint(role_id : int, role_data: RoleRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        request_username = decode_access_token(token)
        request_user = get_user(db, username=request_username)
        if request_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid Token",
            )

        if not has_permission(request_user, "update_role"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        
        updated_role = update_role(role_id=role_id, role_data=role_data, db=db)
        
        if updated_role == True:
            return {"message": f"successfully updated role with role id {role_id}"}
        print(f"update_role in auth {updated_role}")
    except HTTPException as http_exc:
        # If an expected HTTPException occurs, re-raise it as is
        raise http_exc

    except Exception as e:
        # Log the actual error and return an internal server error response
        logging.error(f"Unexpected error getting user roles: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail={str(e)}  # Return the actual error message
        )
        
@router.delete("/delete_role/{role_id}", response_model=dict)
async def delete_role_auth_endpoint(role_id: int, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        request_username = decode_access_token(token)
        request_user = get_user(db, username=request_username)
        if request_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid Token",
            )

        if not has_permission(request_user, "delete_role"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        
        delete = delete_role(role_id, db)
        
        if delete == True:
            return {"message": f"Operation completed successfully"}
    except HTTPException as http_exc:
        # If an expected HTTPException occurs, re-raise it as is
        raise http_exc

    except Exception as e:
        # Log the actual error and return an internal server error response
        logging.error(f"Unexpected error getting user roles: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail={str(e)}  # Return the actual error message
        )

# Permissions

@router.post("/permissions")
async def create_permission(permission:RoleRequest, token: str = Depends(oauth2_scheme),db: Session = Depends(get_db)):
    try:
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
    except Exception as e:
        logging.error(f"Error creating permission: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/permissions")
async def list_permissions(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        user = get_user(db, username=decode_access_token(token))
        if not has_permission(user, "view_permissions"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        permissions = db.query(Permission).all()
        return permissions
    except Exception as e:
        logging.error(f"Error listing permissions: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/assign-permission")
async def assign_permission(assignPermissionRequest:AssignPermissionRequest, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        requesting_user = get_user(db, username=decode_access_token(token))
        if not has_permission(requesting_user, "assign_permissions"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        role = assign_permission_to_role(db, assignPermissionRequest.role_id, assignPermissionRequest.permission_id)
        return {"role": role.name, "permissions": [permission.name for permission in role.permissions]}
    except Exception as e:
        logging.error(f"Error assigning permission: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/get-user-permission-token")
async def list_permissions_for_user_from_token(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        print(f"this is token: {token}")
        username = decode_access_token(token)
        print(f"this is username: {username}")
        user = get_user(db, username=username)
        print(f"this is user: {user}")
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return {"username": user.username, "permissions": get_user_permissions(user)}
    except Exception as e:
        logging.error(f"Error getting user permissions: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/permissions/{user_name}")
async def list_permissions_for_user(user_name:str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
    
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
    
    except Exception as e:
        logging.error(f"Error getting user permissions: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
    

@router.get("/cause-error")
async def cause_error():
    raise Exception("This is a test error from /cause-error")