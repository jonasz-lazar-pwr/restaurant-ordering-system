import httpx
from fastapi import Request, Response

ORDER_SERVICE_URL = "http://order-service:8003"

async def forward_order_request(request: Request, path: str) -> Response:
    url = f"{ORDER_SERVICE_URL}/{path}"
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method=request.method,
            url=url,
            headers=request.headers.raw,
            content=await request.body()
        )
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=dict(response.headers)
    )
