from __future__ import annotations

import logging
import mimetypes
import os

import httpx
from httpx import URL

ENV_API_KEY = 'NODE_IMAGE_API_KEY'


def get_api_key_from_env() -> str:
    return os.getenv(ENV_API_KEY) or ''


def is_url(url: str) -> bool:
    return URL(url).scheme in ['http', 'https']


def download_image_from_url(
        url: str,
        timeout: int = 10,
        logger: logging.Logger | None = None,
) -> tuple[str, bytes, str]:
    if not is_url(url):
        raise ValueError(f'Invalid URL: {url}')

    logger = logger or logging.getLogger(__name__)
    logger.info(f'Downloading image from URL: {url}')

    response = httpx.get(url, timeout=timeout)
    if response.status_code != 200:
        message = (
            f'Failed to download image from URL: {url}, status code: {response.status_code}, body: {response.text}'
        )
        logger.error(message)
        raise ValueError(message)

    content_type = response.headers.get('Content-Type')
    if not content_type:
        content_type = 'image/jpeg'

    ext = mimetypes.guess_extension(content_type)
    if not ext:
        ext = '.jpg'

    return f'image{ext}', response.content, content_type
