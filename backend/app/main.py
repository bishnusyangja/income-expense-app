from fastapi import FastAPI

from app.csrf import CSRFMiddleware, router as csrf_router
from user.api import router as user_router

app = FastAPI(title="Income Expense API")
app.add_middleware(CSRFMiddleware)
app.include_router(csrf_router)
app.include_router(user_router)
