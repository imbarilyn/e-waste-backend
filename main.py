# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


app.include_router(admin.router)
app.include_router(aggregator.router)



@app.on_event('startup')
async def startup():
  await create_tables()

