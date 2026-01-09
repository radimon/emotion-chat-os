from backend.db.engine import engine
from backend.db.base import Base
from ackend.db import models

Base metadata.create_all(bind=engine)

print("Database tables created.")