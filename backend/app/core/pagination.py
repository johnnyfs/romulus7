from fastapi import Request
from pydantic import BaseModel

from logging import getLogger


from base64 import b64decode, b64encode

logger = getLogger("uvicorn.error")


class Cursor(BaseModel):
    offset: int
    limit: int

    def encode(self) -> str:
        bytes_ = self.model_dump_json().encode('utf-8')
        logger.info("Encoding cursor: %s", bytes_)
        encoded = b64encode(bytes_)
        logger.info("Base64 encoded cursor: %s", encoded)
        as_str = encoded.decode('utf-8')
        logger.info("Cursor as string: %s", as_str)
        return as_str

    @classmethod
    def decode(cls, cursor: str) -> 'Cursor':
        logger.info(f"Decoding cursor string: {cursor}")
        bytes_ = cursor.encode('utf-8')
        logger.info("Decoding cursor: %s", bytes_)
        decoded = b64decode(bytes_)
        return Cursor.model_validate_json(decoded)
    
class NextUrlBuilder:
    def __init__(self, request: Request): # Request is injected automatically
        self._request = request

    def from_cursor(self, cursor: str | None) -> str | None:
        if not cursor:
            return None
        
        url = self._request.url
        query_params = dict(self._request.query_params)
        query_params['cursor'] = cursor
        return str(url.include_query_params(**query_params))