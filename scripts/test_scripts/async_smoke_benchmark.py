import asyncio
import json
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from bot.core.archive_manager import archive_manager
from bot.core.media_info import media_info_extractor

TMP = Path('/tmp/mltb_async_smoke')
SRC = TMP / 'payload'
ZIP_PATH = TMP / 'payload.zip'
EXTRACT_DIR = TMP / 'extract'
VIDEO = TMP / 'sample.mp4'
THUMB = TMP / 'sample_thumb.jpg'


def p95(vals):
    if not vals:
        return 0.0
    vals = sorted(vals)
    idx = int(round(0.95 * (len(vals) - 1)))
    return vals[idx]


async def monitor_loop_lag(stop_event, interval=0.02):
    lags = []
    loop = asyncio.get_running_loop()
    expected = loop.time() + interval
    while not stop_event.is_set():
        await asyncio.sleep(interval)
        now = loop.time()
        lags.append(max(0.0, now - expected))
        expected = now + interval
    return lags


async def measure(name, coro):
    stop = asyncio.Event()
    mon_task = asyncio.create_task(monitor_loop_lag(stop))
    start = time.perf_counter()
    ok = True
    err = None
    result = None
    try:
        result = await coro
    except Exception as exc:
        ok = False
        err = str(exc)
    duration = time.perf_counter() - start
    stop.set()
    lags = await mon_task
    return {
        'name': name,
        'ok': ok,
        'duration_s': round(duration, 3),
        'loop_lag_avg_ms': round((statistics.mean(lags) if lags else 0.0) * 1000, 3),
        'loop_lag_p95_ms': round(p95(lags) * 1000, 3),
        'loop_lag_max_ms': round((max(lags) if lags else 0.0) * 1000, 3),
        'error': err,
        'result_summary': str(result)[:220] if result is not None else None,
    }


async def main():
    if TMP.exists():
        shutil.rmtree(TMP)
    SRC.mkdir(parents=True, exist_ok=True)

    payload_file = SRC / 'blob.bin'
    with open(payload_file, 'wb') as handle:
        for _ in range(96):
            handle.write(os.urandom(1024 * 1024))

    results = []

    async def idle_wait():
        await asyncio.sleep(2)

    results.append(await measure('baseline_idle_2s', idle_wait()))
    results.append(await measure(
        'archive_compress_zip',
        archive_manager.compress(str(SRC), str(ZIP_PATH), format='zip', compression_level=6),
    ))

    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    results.append(await measure(
        'archive_extract_zip',
        archive_manager.extract(str(ZIP_PATH), str(EXTRACT_DIR)),
    ))

    ffmpeg_ok = subprocess.call(['bash', '-lc', 'command -v ffmpeg >/dev/null 2>&1']) == 0
    if ffmpeg_ok:
        subprocess.run(
            [
                'ffmpeg', '-y',
                '-f', 'lavfi', '-i', 'testsrc=size=640x360:rate=30',
                '-t', '8',
                str(VIDEO)
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        results.append(await measure(
            'ffmpeg_extract_thumbnail',
            media_info_extractor.extract_thumbnail(str(VIDEO), str(THUMB), '00:00:03'),
        ))
    else:
        results.append({
            'name': 'ffmpeg_extract_thumbnail',
            'ok': False,
            'skipped': True,
            'reason': 'ffmpeg not found in PATH',
        })

    print(json.dumps({'tmp_dir': str(TMP), 'results': results}, indent=2))


if __name__ == '__main__':
    asyncio.run(main())
