from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Reads X-Tenant-ID header and injects into request.state."""

    async def dispatch(self, request: Request, call_next):
        tenant_id = request.headers.get("X-Tenant-ID", "")
        request.state.tenant_id = tenant_id
        response = await call_next(request)
        return response


class OrgScopingMiddleware(BaseHTTPMiddleware):
    """Reads X-Org-Level and X-Org-ODS-Code headers for per-request org context."""

    async def dispatch(self, request: Request, call_next):
        request.state.org_level = request.headers.get("X-Org-Level", "")
        request.state.org_ods_code = request.headers.get("X-Org-ODS-Code", "")
        response = await call_next(request)
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds standard security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response
