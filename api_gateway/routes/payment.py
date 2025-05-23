from fastapi import APIRouter, Request
from services.payment import forward_payment_request

router = APIRouter()

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_payment(request: Request, path: str):
    return await forward_payment_request(request, path)
