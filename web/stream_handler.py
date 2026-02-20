from __future__ import annotations

import aiohttp

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from bot.core.config_manager import Config
from bot.core.stream_proxy import stream_proxy


router = APIRouter()


async def _fetch_file_path(file_id: str) -> str:
    api_url = f"https://api.telegram.org/bot{Config.BOT_TOKEN}/getFile"
    async with aiohttp.ClientSession() as session:
        async with session.get(api_url, params={"file_id": file_id}) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=502, detail="Telegram getFile failed")
            payload = await resp.json()
            if not payload.get("ok"):
                raise HTTPException(status_code=404, detail="File not found")
            file_path = payload.get("result", {}).get("file_path")
            if not file_path:
                raise HTTPException(status_code=404, detail="File path missing")
            return file_path


async def _stream_file(file_url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            if resp.status != 200:
                raise HTTPException(status_code=502, detail="Telegram file download failed")
            async for chunk in resp.content.iter_chunked(1024 * 512):
                yield chunk


@router.get("/stream/{token}")
async def stream_file(token: str):
    payload = await stream_proxy.get_token(token)
    if not payload:
        raise HTTPException(status_code=404, detail="Invalid or expired token")

    file_id = payload.get("file_id")
    if not file_id:
        raise HTTPException(status_code=404, detail="Missing file id")

    file_path = await _fetch_file_path(file_id)
    file_url = f"https://api.telegram.org/file/bot{Config.BOT_TOKEN}/{file_path}"
    mime_type = payload.get("mime_type") or "application/octet-stream"
    file_name = payload.get("file_name") or "download"

    headers = {
        "Content-Disposition": f"attachment; filename=\"{file_name}\""
    }

    return StreamingResponse(
        _stream_file(file_url),
        media_type=mime_type,
        headers=headers,
    )


def add_stream_routes(app):
    app.include_router(router)
