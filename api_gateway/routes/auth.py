from fastapi import APIRouter, Request
from services.auth import forward_auth_request

router = APIRouter()

@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_auth(request: Request, path: str):
    return await forward_auth_request(request, path)
