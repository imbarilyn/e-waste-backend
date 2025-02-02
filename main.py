from fastapi import FastAPI
from app.database import  create_tables
from app.auth import admin, aggregator

app = FastAPI()


app.include_router(admin.router)
app.include_router(aggregator.router)



@app.on_event('startup')
async def startup():
  await create_tables()

