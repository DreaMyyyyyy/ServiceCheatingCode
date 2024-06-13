import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routers import CRouterServiceCheatingCode
from src.config.logging import init_logging

# Настройка логгера
init_logging()

app = FastAPI()

origins = [
	"http://localhost",
    "http://localhost:3000",
	"http://localhost:3001",
    "http://localhost:8080"
]
app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(CRouterServiceCheatingCode.router)

if __name__ == "__main__":
	uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)



