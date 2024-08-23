from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import json

from app.kafka_producer import send_log


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Process the request and get the response
        response = await call_next(request)

        # Extract request details
        request_body = await request.json() if request.method in ("POST", "PUT", "PATCH") else {}
        user_agent = request.headers.get("User-Agent")
        ip_address = request.client.host
        token = request.headers.get("Authorization")

        # Extract response details
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        response.body_iterator = iter([response_body])

        try:
            response_body_json = json.loads(response_body.decode())
        except json.JSONDecodeError:
            response_body_json = {"text": response_body.decode()}

        log_data = {
            "method": request.method,
            "url": str(request.url),
            "user_agent": user_agent,
            "ip_address": ip_address,
            "token": token,
            "request_body": request_body,
            "response_body": response_body_json,
            "status_code": response.status_code,
        }

        send_log( log_data)

        return response
