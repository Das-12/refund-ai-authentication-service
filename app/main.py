from fastapi import FastAPI, Depends
from app.kafka_producer import close_kafka_producer, init_kafka_producer
from sqlalchemy.orm import Session

from app.log_middleware import LoggingMiddleware
from .database import SessionLocal, engine, database, get_db
from .auth.models import Base as AuthBase
from .permissions.models import Base as PermissionsBase, Role, Permission
from .auth.routes import router as auth_router
from .permissions.routes import router as permissions_router
from contextlib import asynccontextmanager
from .auth.models import User
from .auth.auth import get_password_hash


AuthBase.metadata.create_all(bind=engine)
PermissionsBase.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to the database
    await database.connect()
    db = SessionLocal()  # Manually create a session
    
    try:
        # Create the SuperAdmin role and user
        await init_kafka_producer()
        create_superadmin(db)
        create_superadmin_user(db)
        
        yield  # Yield to allow the application to run
        
    finally:
        await close_kafka_producer()
        db.close()  # Close the session
        await database.disconnect()  # Disconnect from the database


def create_superadmin(db: Session):
    # Check if the SuperAdmin role exists
    superadmin_role = db.query(Role).filter(Role.name == "SuperAdmin").first()
    if not superadmin_role:
        # Create the SuperAdmin role
        superadmin_role = Role(name="SuperAdmin", description="SuperAdmin with all permissions")
        db.add(superadmin_role)
        db.commit()
        db.refresh(superadmin_role)

    # Assign all permissions to the SuperAdmin role
    all_permissions = db.query(Permission).all()
    for permission in all_permissions:
        if permission not in superadmin_role.permissions:
            superadmin_role.permissions.append(permission)
    
    db.commit()


def create_superadmin_user(db: Session):
    # Check if the SuperAdmin user exists
    superadmin_user = db.query(User).filter(User.username == "superadmin").first()
    if not superadmin_user:
        # Create the SuperAdmin user
        superadmin_user = User(
            username="superadmin",
            hashed_password=get_password_hash("superadmin_password")  # Secure this in production!
        )
        db.add(superadmin_user)
        db.commit()
        db.refresh(superadmin_user)
    
    # Assign the SuperAdmin role to the user
    superadmin_role = db.query(Role).filter(Role.name == "SuperAdmin").first()
    if superadmin_role not in superadmin_user.roles:
        superadmin_user.roles.append(superadmin_role)
        db.commit()
        db.refresh(superadmin_user)

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router, prefix="/auth")
app.include_router(permissions_router, prefix="/permissions")
app.add_middleware(LoggingMiddleware)

