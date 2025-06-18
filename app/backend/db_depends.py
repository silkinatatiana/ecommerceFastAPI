from app.backend.db import Base


async def get_db():
    db = Base.SessionLocal()
    try:
        yield db
    finally:
        db.close()
