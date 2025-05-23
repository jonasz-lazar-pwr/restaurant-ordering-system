import httpx
from fastapi import Request, Response
from starlette.responses import JSONResponse

AUTH_SERVICE_URL = "http://auth-service:8002"

async def forward_auth_request(request: Request, path: str) -> Response:
    url = f"{AUTH_SERVICE_URL}/{path}"
    try:
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
    except httpx.RequestError as e:
        return JSONResponse(status_code=502, content={"detail": str(e)})
