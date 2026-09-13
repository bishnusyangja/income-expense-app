from fastapi import FastAPI

from app.csrf import CSRFMiddleware, router as csrf_router
from app.exceptions import register_exception_handlers
from user.api import router as user_router

app = FastAPI(title="Income Expense API")
register_exception_handlers(app)
app.add_middleware(CSRFMiddleware)
app.include_router(csrf_router)
app.include_router(user_router)
