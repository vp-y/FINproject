from database.connection import Base, engine
from database import models


Base.metadata.create_all(
    bind=engine
)


print(
    "Database initialized"
)