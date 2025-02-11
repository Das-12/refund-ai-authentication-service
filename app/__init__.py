from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

from app.auth.models import *
from app.permissions.models import *
from app.subscriptions.models import *