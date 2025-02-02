# This is a sample Python script.

app = FastAPI()


app.include_router(admin.router)
app.include_router(aggregator.router)



@app.on_event('startup')
async def startup():
  await create_tables()

