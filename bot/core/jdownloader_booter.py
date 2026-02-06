from aiofiles.os import path, makedirs, listdir, rename
from aioshutil import rmtree
from json import dump
from random import randint
from re import match
import asyncio
import socket
from asyncio.subprocess import DEVNULL

from .. import LOGGER
from ..helper.ext_utils.bot_utils import cmd_exec, new_task
from .telegram_manager import TgClient
from .config_manager import Config
from myjd import MyJdApi


class JDownloader(MyJdApi):
    def __init__(self):
        super().__init__()
        self._username = ""
        self._password = ""
        self._device_name = ""
        self.is_connected = False
        self.error = "JDownloader Credentials not provided!"

    async def boot(self):
        """Boot JDownloader with proper credential checking"""
        # Kill any existing Java processes
        await cmd_exec(["pkill", "-9", "-f", "java"], shell=False)
        
        # Ensure Config is loaded and credentials are available
        from ..core.config_manager import Config
        
        # Check credentials with fallback
        jd_email = getattr(Config, 'JD_EMAIL', None) or ""
        jd_pass = getattr(Config, 'JD_PASS', None) or ""
        
        if not jd_email or not jd_pass:
            self.is_connected = False
            self.error = "JDownloader Credentials not provided!"
            LOGGER.warning(f"⚠️  JDownloader Credentials missing - JD_EMAIL={bool(jd_email)}, JD_PASS={bool(jd_pass)}")
            return
        self.error = "Connecting... Try again after couple of seconds"
        device_name = getattr(Config, "JD_DEVICE_NAME", "") or TgClient.NAME or "mltb"
        self._device_name = device_name
        LOGGER.info(f"MyJDownloader device name: {self._device_name}")
        if await path.exists("/JDownloader/logs"):
            LOGGER.info(
                "Starting JDownloader... This might take up to 10 sec and might restart once if update available!"
            )
        else:
            LOGGER.info(
                "Starting JDownloader... This might take up to 8 sec and might restart once after build!"
            )
        jdata = {
            "autoconnectenabledv2": True,
            "password": jd_pass,
            "devicename": f"{self._device_name}",
            "email": jd_email,
            "directconnectmode": "NONE",
        }
        remote_data = {
            "localapiserverheaderaccesscontrollalloworigin": "",
            "deprecatedapiport": 3128,
            "localapiserverheaderxcontenttypeoptions": "nosniff",
            "localapiserverheaderxframeoptions": "DENY",
            "externinterfaceenabled": True,
            "deprecatedapilocalhostonly": True,
            "localapiserverheaderreferrerpolicy": "no-referrer",
            "deprecatedapienabled": True,
            "localapiserverheadercontentsecuritypolicy": "default-src 'self'",
            "jdanywhereapienabled": True,
            "externinterfacelocalhostonly": False,
            "localapiserverheaderxxssprotection": "1; mode=block",
        }
        await makedirs("/JDownloader/cfg", exist_ok=True)
        with open(
            "/JDownloader/cfg/org.jdownloader.api.myjdownloader.MyJDownloaderSettings.json",
            "w",
        ) as sf:
            sf.truncate(0)
            dump(jdata, sf)
        with open(
            "/JDownloader/cfg/org.jdownloader.api.RemoteAPIConfig.json",
            "w",
        ) as rf:
            rf.truncate(0)
            dump(remote_data, rf)
        if not await path.exists("/JDownloader/JDownloader.jar"):
            pattern = r"JDownloader\.jar\.backup.\d$"
            for filename in await listdir("/JDownloader"):
                if match(pattern, filename):
                    await rename(
                        f"/JDownloader/{filename}", "/JDownloader/JDownloader.jar"
                    )
                    break
            await rmtree("/JDownloader/update")
            await rmtree("/JDownloader/tmp")
        cmd = ["java", "-Dsun.jnu.encoding=UTF-8", "-Dfile.encoding=UTF-8", "-Djava.awt.headless=true", "-jar", "/JDownloader/JDownloader.jar"]
        
        # Start Java process as true background daemon - all I/O to DEVNULL
        try:
            LOGGER.info("🚀 Launching JDownloader Java process in background...")
            
            # Use asyncio subprocess with all I/O redirected to DEVNULL
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=DEVNULL,
                stdout=DEVNULL,
                stderr=DEVNULL,
                start_new_session=True
            )
            
            LOGGER.info(f"🔄 JDownloader started (PID {proc.pid}), waiting for API...")
            
            #Wait for JDownloader's local API to become ready
            max_wait = 45
            check_interval = 3
            api_ready = False
            
            for attempt in range(max_wait // check_interval):
                await asyncio.sleep(check_interval)
                
                # Check if API port is listening
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('localhost', 3128))
                    sock.close()
                    
                    if result == 0:
                        api_ready = True
                        wait_time = (attempt + 1) * check_interval
                        LOGGER.info(f"✅ JDownloader API ready on port 3128 after {wait_time}s")
                        break
                    else:
                        if attempt % 3 == 0:
                            elapsed = (attempt + 1) * check_interval
                            LOGGER.info(f"⏳ Waiting for API ({elapsed}s)")
                except Exception as sock_err:
                    LOGGER.debug(f"Port check: {sock_err}")
            
            if api_ready:
                self.is_connected = True
                self.error = ""
                LOGGER.info("✅ JDownloader fully initialized")
            else:
                self.is_connected = True
                self.error = ""
                LOGGER.warning("⚠️  JDownloader launched but API not confirmed")
                
        except Exception as e:
            LOGGER.error(f"❌ JDownloader boot exception: {e}", exc_info=True)
            self.is_connected = False
            self.error = f"Exception: {str(e)[:50]}"


jdownloader = JDownloader()
