from __future__ import annotations

import aiohttp

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from logging import getLogger

from bot.core.config_manager import Config
from bot.core.stream_proxy import stream_proxy


router = APIRouter()
LOGGER = getLogger(__name__)


async def _fetch_file_path(file_id: str) -> str:
    api_url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/getFile"
    LOGGER.debug(f"Stream: Fetching file_path for file_id={file_id[:20]}...")
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, params={"file_id": file_id}) as resp:
            LOGGER.debug(f"Stream: Telegram getFile status={resp.status}")
            if resp.status != 200:
                body = await resp.text()
                LOGGER.error(f"Stream: Telegram getFile failed status={resp.status} body={body[:500]}")
                raise HTTPException(status_code=502, detail="Telegram getFile failed")
            payload = await resp.json()
            LOGGER.debug(f"Stream: Telegram getFile payload ok={payload.get('ok')}")
            if not payload.get("ok"):
                error_code = payload.get("error_code")
                error_desc = payload.get("description", "Unknown error")
                LOGGER.warning(f"Stream: Telegram getFile returned error code={error_code} desc={error_desc}")
                # For file too big errors, we still need the file_path if available
                if error_code == 400 and "too big" in error_desc.lower():
                    # Try to proceed with large file streaming
                    result = payload.get("result")
                    if isinstance(result, dict):
                        file_path = result.get("file_path")
                        if file_path:
                            LOGGER.info(f"Stream: Large file detected, using file_path={file_path[:50]}...")
                            return file_path
                    raise HTTPException(
                        status_code=413, 
                        detail="File too large for streaming (>20MB). Telegram Bot API has a 20MB file size limit."
                    )
                raise HTTPException(status_code=404, detail=f"Telegram error: {error_desc}")
            file_path = payload.get("result", {}).get("file_path")
            if not file_path:
                LOGGER.warning(f"Stream: Telegram getFile missing file_path: {payload}")
                raise HTTPException(status_code=404, detail="File path missing")
            LOGGER.debug(f"Stream: Got file_path={file_path[:50]}...")
            return file_path


async def _stream_file(file_url: str):
    """Stream file from Telegram CDN"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    LOGGER.error(f"Stream: Telegram CDN download failed status={resp.status} body={body[:200]}")
                    raise HTTPException(status_code=502, detail="Telegram file download failed")
                async for chunk in resp.content.iter_chunked(1024 * 512):
                    yield chunk
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Stream file CDN error: {e}")
        raise HTTPException(status_code=500, detail="Stream error")


async def _stream_file_pyrogram(file_id: str):
    """Placeholder for future Pyrogram-based streaming"""
    LOGGER.warning("Stream: Pyrogram streaming not yet implemented")
    raise HTTPException(
        status_code=413, 
        detail="File too large for streaming. Telegram Bot API has a 20MB file size limit. Please use a smaller file."
    )


@router.get("/stream/{token}")
async def stream_file(token: str):
    LOGGER.info(f"Stream: Incoming request for token={token[:20]}...")
    payload = await stream_proxy.get_token(token)
    if not payload:
        LOGGER.warning(f"Stream: Token not found or expired: {token}")
        raise HTTPException(status_code=404, detail="Invalid or expired token")

    file_id = payload.get("file_id")
    if not file_id:
        LOGGER.error(f"Stream: Payload missing file_id: {payload}")
        raise HTTPException(status_code=404, detail="Missing file id")

    LOGGER.debug(f"Stream: file_id from payload={file_id[:30]}...")
    mime_type = payload.get("mime_type") or "application/octet-stream"
    file_name = payload.get("file_name") or "download"

    headers = {
        "Content-Disposition": f"attachment; filename=\"{file_name}\""
    }

    # Try Bot API getFile
    LOGGER.debug(f"Stream: Attempting Bot API download...")
    file_path = await _fetch_file_path(file_id)
    file_url = f"https://api.telegram.org/file/bot{Config.BOT_TOKEN}/{file_path}"
    LOGGER.info(f"Stream: Starting Bot API stream for {file_name}")
    return StreamingResponse(
        _stream_file(file_url),
        media_type=mime_type,
        headers=headers,
    )


def add_stream_routes(app):
    app.include_router(router)
