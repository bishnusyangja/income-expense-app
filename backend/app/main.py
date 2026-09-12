from fastapi import FastAPI

from user.api import router as user_router

app = FastAPI(title="Income Expense API")
app.include_router(user_router)
