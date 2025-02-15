from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.database import  create_tables
from app.auth import auth_admin, auth_aggregator

app = FastAPI()

app.mount('/products_images/uploads', StaticFiles(directory='products_images/uploads'), name='uploads')


app.add_middleware(
  CORSMiddleware,
  allow_origins=['*'],
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*']
)


app.include_router(auth_admin.router)
app.include_router(auth_aggregator.router)

from app.routers import admin, aggregator

app.include_router(aggregator.router)
app.include_router(admin.router)



@app.on_event('startup')
async def startup():
  await create_tables()


