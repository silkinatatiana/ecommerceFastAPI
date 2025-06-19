from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.routers import category, products, reviews
from app.backend.db import Base, engine, async_session_maker
from app.routers import auth, permission

app = FastAPI()
app.include_router(auth.router)
app.include_router(permission.router)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        yield session


@app.get('/')
async def welcome() -> dict:
    return {'message': 'My e-commerce app'}


app.include_router(
    category.router,
    dependencies=[Depends(get_db)]
)
app.include_router(
    products.router,
    dependencies=[Depends(get_db)]
)
app.include_router(
    reviews.router,
    dependencies=[Depends(get_db)]
)