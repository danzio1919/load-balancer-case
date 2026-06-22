from fastapi import APIRouter
from api.servers import router as servers_router
from api.simulate import router as simulate_router

api_router = APIRouter()
api_router.include_router(servers_router)
api_router.include_router(simulate_router)
