from fastapi import FastAPI, Request
from app.kafka_producer import close_kafka_producer, init_kafka_producer
from sqlalchemy.orm import Session
from aiokafka import AIOKafkaConsumer
from .kafka_consumer import update_subscription_count
from app.log_middleware import LoggingMiddleware
from .database import SessionLocal, engine, database
from .auth.models import Base as AuthBase
from .permissions.models import Base as PermissionsBase, Role, Permission
from .auth.routes import router as auth_router
from .permissions.routes import router as permissions_router
from contextlib import asynccontextmanager
from .subscriptions.routes import router as subscriptions_router
from .auth.models import User
from .auth.auth import get_password_hash
from fastapi.responses import JSONResponse
import traceback
import asyncio
from .kafka_producer import send_app_error
from .config import settings

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
        create_roles_and_permissions(db)
        create_superadmin_user(db)
        retries = 10
        consumer = None
        while retries > 0:
            try:
                consumer = AIOKafkaConsumer(
                    settings.KAFKA_COUNT_TOPIC,
                    bootstrap_servers=settings.KAFKA_BROKER_URL,
                    group_id='count-group',
                    auto_offset_reset='earliest',
                    enable_auto_commit=True,              
                )
                print('auth consumer started')
                break
            except Exception as e:
                print('failed starting consumer')
                retries -= 1
                await asyncio.sleep(10)
                
        if consumer is None:
            raise Exception("Failed to start Kafka consumer")
        

        task = asyncio.create_task(update_subscription_count(consumer=consumer))
        
        try:
            yield
        finally:
            task.cancel()
            await asyncio.wait_for(task, timeout=5)
            
    finally:
        await close_kafka_producer()
        db.close()  # Close the session
        await database.disconnect()  # Disconnect from the database

def create_superadmin_user(db: Session):
    # Check if the SuperAdmin user exists
    superadmin_user = db.query(User).filter(User.username == "superadmin").first()
    if not superadmin_user:
        # Create the SuperAdmin user
        superadmin_user = User(
            username="superadmin",
            hashed_password=get_password_hash("123456")  # Secure this in production!
        )
        db.add(superadmin_user)
        db.commit()
        db.refresh(superadmin_user)
    
    # Assign the SuperAdmin role to the user
    superadmin_role = db.query(Role).filter(Role.name == "super_admin").first()
    if superadmin_role not in superadmin_user.roles:
        superadmin_user.roles.append(superadmin_role)
        db.commit()
        db.refresh(superadmin_user)

def create_roles_and_permissions(db:Session):
    all_permissions = [
        "Create Company",
            "Create User",
            "Update Company",
            "Update User",
            "Delete Company",
            "Delete User",
            "View Company",
            "View User",
            "Create Permission",
            "Create Role",
            "Update Permission",
            "Update Role",
            "Delete Permission",
            "Delete Role",
            "Assign Role",
            "Assign Permission",
            "Get Permission of User",
            "Get Permission Under Roles",
            "Get Timeline",
            "Get Users Under Company",
            "Update User Under Company",
            "Create User Under Company",
            "View Roles of User",
            "Assign Permissions",
            "View Permissions",
            "View Roles",
            "Create Plan",
            "View Plans",
            "Update Plan",
            "Delete Plan",
            "Create Subscription",
            "View Subscriptions",
            "Update Subscription",
            "Delete Subscription"
    ]
    
    for permission in all_permissions:
        permissionModel = db.query(Permission).filter(Permission.name == make_key(permission)).first()
        if not permissionModel:
            permissionModel = Permission(
                name=make_key(permission),
                description = permission
            )
            db.add(permissionModel)
            db.commit()
            db.refresh(permissionModel)
        
    roles = [{
        "role":"super_admin",
        "permissions":[
            "Create Company",
            "Create User",
            "Update Company",
            "Update User",
            "Delete Company",
            "Delete User",
            "View Company",
            "View User",
            "Create Permission",
            "Create Role",
            "Update Permission",
            "Update Role",
            "Delete Permission",
            "Delete Role",
            "Assign Role",
            "Assign Permission",
            "Get Permission of User",
            "Get Permission Under Roles",
            "Get Timeline",
            "View Roles of User",
            "Assign Permissions",
            "View Permissions",
            "View Roles",
            "Create Plan",
            "View Plans",
            "Update Plan",
            "Delete Plan",
            "Create Subscription",
            "View Subscriptions",
            "Update Subscription",
            "Delete Subscription"
        ]
    },{
        "role":"company",
        "permissions":[
            "Get Timeline",
            "Get Users Under Company",
            "Update User Under Company",
            "Create User Under Company"
        ]
    },{
        "role":"staff",
        "permissions":[
            "Get Timeline"
        ]
    }]
    for role in roles:  
        roleModel = db.query(Role).filter(Role.name == role['role']).first()
        if not roleModel:
            roleModel = Role(
                name=role['role'],
                description = role['role']
            )
            db.add(roleModel)
            db.commit()
            db.refresh(roleModel)

        for permission in role['permissions']:
            permissionModel = db.query(Permission).filter(Permission.name == make_key(permission)).first()
            if permissionModel not in roleModel.permissions:
                roleModel.permissions.append(permissionModel)
                db.commit()
                db.refresh(roleModel)

def make_key(val:str):
    return val.replace(" ","_").lower()
app = FastAPI(lifespan=lifespan)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that logs unhandled exceptions to Kafka.
    """
    error_log = {
        "error_message": str(exc),
        "stack_trace": traceback.format_exc(),
        "path": request.url.path,
        "method": request.method,
        "client": request.client.host if request.client else "unknown",
    }
    asyncio.create_task(send_app_error(error_log))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please contact support."}
    )

app.include_router(auth_router, prefix="/auth")
app.include_router(permissions_router, prefix="/permissions")
app.include_router(subscriptions_router, prefix="/subscriptions")
app.add_middleware(LoggingMiddleware)

