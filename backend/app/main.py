from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.csrf import CSRFMiddleware, router as csrf_router
from app.exceptions import register_exception_handlers
from finance.api import router as finance_router
from user.api import router as user_router

app = FastAPI(title="Income Expense API")
register_exception_handlers(app)
app.add_middleware(CSRFMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(csrf_router)
app.include_router(user_router)
app.include_router(finance_router)
