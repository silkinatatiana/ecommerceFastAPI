from fastapi import FastAPI
from app.routers import category, products
from app.backend.db import Base


app = FastAPI()
base = Base()

@app.on_event("startup")
def startup():
    base.metadata.create_all(bind=base.engine)

@app.get('/')
async def welcome() -> dict:
    return {'message': 'My e-commerce app'}

app.include_router(category.router)
app.include_router(products.router)