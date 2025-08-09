from __future__ import annotations

import logging
from pathlib import Path

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self

import httpx
from httpx import Timeout

from ._utils import download_image_from_url
from ._utils import get_api_key_from_env
from ._utils import is_url

DEFAULT_BASE_URL = 'https://api.nodeimage.com'

DEFAULT_TIMEOUT = Timeout(10)

HEADER_API_KEY = 'X-API-Key'


class Client:
    def __init__(
            self,
            api_key: str,
            base_url: str = DEFAULT_BASE_URL,
            timeout: float | Timeout | None = DEFAULT_TIMEOUT,
            logger: logging.Logger | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = Timeout(timeout)
        self.logger = logger or logging.getLogger(__name__)

    @classmethod
    def from_env(cls, logger: logging.Logger | None = None) -> Self:
        return cls(get_api_key_from_env(), logger=logger)

    def _get_headers(self) -> dict:
        return {HEADER_API_KEY: self.api_key}

    def _get_url(self, path: str) -> str:
        return f'{self.base_url}/{path}'

    def _request(self, method: str, url: str, **kwargs) -> dict:
        response = httpx.request(
            method=method,
            url=url,
            headers=self._get_headers(),
            timeout=self.timeout,
            **kwargs,
        )
        if response.status_code != 200:
            raise ValueError(f'Request failed status_code={response.status_code}, body={response.text}')
        return response.json()

    def get_images(self) -> dict:
        url = self._get_url('api/v1/list')
        return self._request('GET', url)

    def upload_image(self, image_path_or_url: str | Path) -> dict:
        url = self._get_url('api/upload')
        if isinstance(image_path_or_url, str) and is_url(image_path_or_url):
            image_url = image_path_or_url
            return self._request('POST', url, files={'image': download_image_from_url(image_url)})
        else:
            self.logger.info(f'Reading image from local path: {image_path_or_url}')
            image_path = Path(image_path_or_url)
            if image_path.is_file():
                with open(image_path, 'rb') as image:
                    return self._request('POST', url, files={'image': image})
            else:
                raise ValueError(f'Invalid image path: {image_path}')

    def delete_image(self, image_id: str) -> dict:
        if not image_id:
            raise ValueError('image_id is required')
        url = f'{self.base_url}/api/v1/delete/{image_id}'
        return self._request('DELETE', url)
