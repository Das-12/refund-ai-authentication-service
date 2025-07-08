# from fastapi import Request
# from fastapi.responses import JSONResponse, PlainTextResponse, Response
# from starlette.middleware.base import BaseHTTPMiddleware,_StreamingResponse
# from starlette.responses import StreamingResponse

# import json
# import traceback
# from app.kafka_producer import send_log
# import asyncio
# import logging

# logger = logging.getLogger(__name__)

# class LoggingMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         # Process the request and get the response
#         try:
#             request_body = await request.json()
#         except json.JSONDecodeError:
#             request_body = None  # Handle non-JSON bodies
#         except Exception:
#             request_body = None  # Handle cases where the body is empty or another error occurs

#         log_data = {
#             'method': request.method,
#             'url': str(request.url),
#             'user_agent': request.headers.get('User-Agent'),
#             'ip_address': request.client.host,
#             'token': request.headers.get('Authorization'),
#             'request_body': request_body,
#         }

#         try:
#             response = await call_next(request)
#         except Exception as e:
#             # Log the exception and stack trace
#             log_data['status_code'] = 500
#             log_data['response_body'] = str(e)
#             log_data['stack_trace'] = traceback.format_exc()

#             # Send the log data to Kafka
#             asyncio.create_task(send_log(log_data))

#             # Re-raise the exception to let FastAPI handle it
#             raise e

#         response_body = None

#         print(type(response))
#         print(type(StreamingResponse))

#         if isinstance(response, JSONResponse):
#             # Read the response body (it should be JSON)
#             response_body = json.dumps(response.body.decode('utf-8'))
#         elif isinstance(response, StreamingResponse):
#             # Handle StreamingResponse (you can adjust this if not needed)
#             content = b""
#             async for chunk in response.body_iterator:
#                 content += chunk
#             response_body = content.decode('utf-8')
#             # Rebuild the streaming response
#             response = StreamingResponse(
#                 iter([content]),
#                 status_code=response.status_code,
#                 headers=dict(response.headers),
#                 media_type=response.media_type
#             )
#         elif isinstance(response, _StreamingResponse):
#             # Handle StreamingResponse (you can adjust this if not needed)
#             content = b""
#             async for chunk in response.body_iterator:
#                 content += chunk
#             response_body = content.decode('utf-8')
#             response = StreamingResponse(
#                 iter([content]),  # Re-stream the captured content
#                 status_code=response.status_code,
#                 headers=dict(response.headers),  # Keep original headers
#                 media_type=response.media_type,
#             )

#             # It's important to remove or adjust the Content-Length header for StreamingResponse
#             if 'content-length' in response.headers:
#                 del response.headers['content-length']


#         # Add response data to the log
#         log_data['response_body'] = response_body
#         log_data['status_code'] = response.status_code

#         # Send the log asynchronously to Kafka
#         asyncio.create_task(send_log(log_data))

#         return response

from fastapi import Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware, _StreamingResponse
import json
import asyncio
import traceback
from app.kafka_producer import send_log
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            request_body = await request.json()
        except (json.JSONDecodeError, Exception):
            request_body = None

        log_data = {
            'method': request.method,
            'url': str(request.url),
            'user_agent': request.headers.get('User-Agent'),
            'ip_address': request.client.host,
            'token': request.headers.get('Authorization'),
            'request_body': request_body,
            'service': 'authentication_micro_service',
            'timestamp': datetime.now(ZoneInfo("Asia/Kolkata")).isoformat(),
        }

        try:
            response = await call_next(request)
        except Exception as e:
            # Let the global exception handler manage the error logging.
            raise e

        response_body = None
        if isinstance(response, JSONResponse):
            response_body = json.dumps(response.body.decode('utf-8'))
        elif isinstance(response, StreamingResponse):
            content = b""
            async for chunk in response.body_iterator:
                content += chunk
            response_body = content.decode('utf-8')
            response = StreamingResponse(
                iter([content]),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        elif isinstance(response, _StreamingResponse):
            content = b""
            async for chunk in response.body_iterator:
                content += chunk
            response_body = content.decode('utf-8')
            response = StreamingResponse(
                iter([content]),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
            if 'content-length' in response.headers:
                del response.headers['content-length']

        log_data['response_body'] = response_body
        log_data['status_code'] = response.status_code

        # Send the normal log only for successful responses
        asyncio.create_task(send_log(log_data))
        return response