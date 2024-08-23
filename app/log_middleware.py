from fastapi import Request
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
import json
import traceback
from app.kafka_producer import send_log


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Process the request and get the response
        
        try:
            request_body = await request.json()# Await the coroutine to get the actual JSON body
        except json.JSONDecodeError:
            request_body = None  

        log_data = {
            'method': request.method,
            'url': str(request.url),
            'user_agent': request.headers.get('User-Agent'),
            'ip_address': request.client.host,
            'token': request.headers.get('Authorization'),
            'request_body': request_body,  # Now this is the actual JSON data
        }

        try:
            response = await call_next(request)
        except Exception as e:
            # Log the exception and stack trace
            log_data['status_code'] = 500
            log_data['response_body'] = str(e)
            log_data['stack_trace'] = traceback.format_exc()

            # Send the log data to Kafka
            send_log(log_data)

            # Re-raise the exception to let FastAPI handle it
            raise e


        if isinstance(response, StreamingResponse):
            # Capture the streamed response content
            content = b''
            async for chunk in response.body_iterator:
                content += chunk
            response_body = content.decode('utf-8')
            # Return a new StreamingResponse with the captured content
            response = StreamingResponse(iter([content]), status_code=response.status_code, headers=dict(response.headers))
        else:
            # For non-streaming responses, just decode the body
            response_body = response.body.decode('utf-8') if response.body else None

        log_data['response_body'] = response_body
        log_data['status_code'] = response.status_code

        send_log( log_data)

        return response
