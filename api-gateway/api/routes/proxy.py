# api/routes/proxy.py

import httpx
import json
from typing import Optional, Dict, List
from fastapi import APIRouter, Request, HTTPException, Response, Depends
from fastapi.security import HTTPAuthorizationCredentials
from ..core.config import settings
from ..core.auth import JWTBearer, verify_jwt_token

router = APIRouter()

# Define paths that DO NOT require JWT authorization
# Remember, these are paths AFTER /api/, e.g., "auth/register"
PUBLIC_PATHS_PREFIXES = [
    "auth/health",
    "auth/register",
    "auth/jwt/login",
    "order/health",
    "order/scan_qr/"
]

SERVICE_ROLE_ACCESS: Dict[str, List[str]] = {
    "auth": ["client", "waiter", "chef", "admin"],
    "order": ["client", "waiter", "admin"],
    "payment": ["client", "admin"],
}


@router.api_route(
    "/{full_path:path}",  # Captures e.g., api/auth/register, api/order/items
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    summary="Proxy endpoint",
    description="Proxies the request to the appropriate microservice based on the path."
)
async def proxy(
        full_path: str,
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(JWTBearer(auto_error=False))
):
    # 1. Extract request data
    method = request.method
    query_params = request.query_params
    body = await request.body()
    outgoing_headers = {k: v for k, v in request.headers.items() if k.lower() != 'host'}

    path_segments = full_path.split('/', 1)
    service_prefix = path_segments[0] if path_segments else ""

    # 2. Check if the path is public
    is_public_path = any(full_path.startswith(public_prefix) for public_prefix in PUBLIC_PATHS_PREFIXES)

    if not is_public_path:
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated. Token is missing or invalid format.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = credentials.credentials
        user_payload = verify_jwt_token(token)

        if not user_payload:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired token.",
                headers={"WWW-Authenticate": "Bearer error=\"invalid_token\""},
            )

        user_role = user_payload.get("role")
        allowed_roles_for_service = SERVICE_ROLE_ACCESS.get(service_prefix)

        if not user_role:
            print(f"Warning: 'role' not found in JWT payload for user {user_payload.get('sub')}")
            raise HTTPException(status_code=403, detail="Access denied. User role missing in token.")

        if allowed_roles_for_service is None:
            print(f"Warning: No roles configured for service prefix '{service_prefix}'. Denying access.")
            raise HTTPException(status_code=403, detail=f"Access denied. Service '{service_prefix}' access not configured.")

        if user_role not in allowed_roles_for_service:
            print(f"Forbidden: User role '{user_role}' not allowed for service '{service_prefix}'. Path: {full_path}")
            raise HTTPException(status_code=403, detail=f"Access denied. You do not have permission to access this resource.")

        outgoing_headers["X-User-Payload"] = json.dumps(user_payload)
        print(f"Authorized user (sub): {user_payload.get('sub')}, role: {user_role}, for path: {full_path}")
    else:
        print(f"Public path accessed: {full_path}")

    # 3. Determine target microservice for routing
    service_host = None
    service_port = None

    if full_path.startswith("auth/"):
        service_host = settings.AUTH_SERVICE_HOST
        service_port = settings.AUTH_SERVICE_PORT
    elif full_path.startswith("order/"):
        service_host = settings.ORDER_SERVICE_HOST
        service_port = settings.ORDER_SERVICE_PORT
    elif full_path.startswith("payment/"):
        service_host = settings.PAYMENT_SERVICE_HOST
        service_port = settings.PAYMENT_SERVICE_PORT
    else:
        if not is_public_path:
            raise HTTPException(status_code=404, detail=f"Unknown service prefix for routing: {service_prefix}")

    if not (service_host and service_port):
        if not is_public_path or (is_public_path and service_prefix in SERVICE_ROLE_ACCESS.keys()):
            print(f"Error: Service configuration missing for service prefix '{service_prefix}'. Path: {full_path}")
            raise HTTPException(status_code=500, detail=f"Service configuration error for proxy to '{service_prefix}'.")

    # 4. Build target URL
    target_url = ""
    if service_host and service_port:
        target_url = f"http://{service_host}:{service_port}/{full_path}"
    else:
        if not is_public_path or service_prefix in SERVICE_ROLE_ACCESS.keys():
            print(f"Error: Failed to determine target URL for {full_path} (service prefix: {service_prefix}).")
            raise HTTPException(status_code=500, detail="Internal routing configuration error: Target URL not determined.")

    headers_for_httpx = {
        k: v for k, v in outgoing_headers.items() if k.lower() != 'content-length'
    }

    # 5. Forward request
    try:
        async with httpx.AsyncClient() as client:
            request_kwargs = {
                "method": method,
                "url": target_url,
                "params": query_params,
                "headers": headers_for_httpx,
                "timeout": 30.0,
                "follow_redirects": True,
            }

            if body:
                # Use the original incoming request's content-type to decide how to handle the body
                original_content_type = request.headers.get("content-type", "").lower()
                if "application/json" in original_content_type:
                    try:
                        request_kwargs["json"] = json.loads(body.decode() if body else "{}")
                    except json.JSONDecodeError:
                        print(f"Warning: JSON body decode error for {target_url}, forwarding as raw bytes.")
                        request_kwargs["content"] = body
                else:
                    request_kwargs["content"] = body

            proxy_response = await client.request(**request_kwargs)

        response_headers = {
            k: v for k, v in proxy_response.headers.items() if
            k.lower() not in ["content-encoding", "transfer-encoding", "connection"]
        }

        return Response(
            content=proxy_response.content,
            status_code=proxy_response.status_code,
            headers=response_headers,
            media_type=proxy_response.headers.get("content-type")
        )
    except httpx.ConnectError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {target_url} - {str(e)}")
    except httpx.TimeoutException as e:
        raise HTTPException(status_code=504, detail=f"Gateway timeout contacting service: {target_url} - {str(e)}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Bad gateway, error contacting service: {target_url} - {str(e)}")
    except Exception as e:
        print(f"Unexpected error in proxy: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error in API Gateway.")
