from fastapi import APIRouter, Request
from services.order import forward_order_request

router = APIRouter()

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_order(request: Request, path: str):
    return await forward_order_request(request, path)
