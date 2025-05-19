import httpx
from fastapi import Request, Response

PAYMENT_SERVICE_URL = "http://payment-service:8004"

async def forward_payment_request(request: Request, path: str) -> Response:
    url = f"{PAYMENT_SERVICE_URL}/{path}"
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
