import asyncio
import socket
from asyncio.subprocess import DEVNULL
from json import dump
from re import match

from aiofiles.os import listdir, makedirs, path, rename
from aioshutil import rmtree

from integrations.myjd import MyJdApi

from .. import LOGGER
from ..helper.ext_utils.bot_utils import cmd_exec
from .telegram_manager import TgClient


class JDownloader(MyJdApi):
    def __init__(self):
        super().__init__()
        self._username = ""
        self._password = ""
        self._device_name = ""
        self.is_connected = False
        self.error = "JDownloader Credentials not provided!"

    def _validate_jd_credentials(self):
        from ..core.config_manager import Config
        jd_email = getattr(Config, 'JD_EMAIL', None) or ""
        jd_pass = getattr(Config, 'JD_PASS', None) or ""
        
        if not jd_email or not jd_pass:
            self.is_connected = False
            self.error = "JDownloader Credentials not provided!"
            LOGGER.warning(f"⚠️  JDownloader Credentials missing - JD_EMAIL={bool(jd_email)}, JD_PASS={bool(jd_pass)}")
            return None, None
        return jd_email, jd_pass

    def _get_device_name(self):
        from ..core.config_manager import Config
        device_name = getattr(Config, "JD_DEVICE_NAME", "") or (TgClient.NAME if TgClient and hasattr(TgClient, 'NAME') else None) or "mltb"
        self._device_name = device_name
        LOGGER.info(f"MyJDownloader device name: {self._device_name}")
        return device_name

    async def _log_startup_message(self):
        if await path.exists("/JDownloader/logs"):
            LOGGER.info("Starting JDownloader... This might take up to 10 sec and might restart once if update available!")
        else:
            LOGGER.info("Starting JDownloader... This might take up to 8 sec and might restart once after build!")

    async def _create_config_files(self, jd_email, jd_pass, device_name):
        jdata = {
            "autoconnectenabledv2": True,
            "password": jd_pass,
            "devicename": f"{device_name}",
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
        await asyncio.to_thread(
            self._write_json_file,
            "/JDownloader/cfg/org.jdownloader.api.myjdownloader.MyJDownloaderSettings.json",
            jdata,
        )
        await asyncio.to_thread(
            self._write_json_file,
            "/JDownloader/cfg/org.jdownloader.api.RemoteAPIConfig.json",
            remote_data,
        )

    async def _prepare_jar_file(self):
        if await path.exists("/JDownloader/JDownloader.jar"):
            return
        pattern = r"JDownloader\.jar\.backup.\d$"
        for filename in await listdir("/JDownloader"):
            if match(pattern, filename):
                await rename(
                    f"/JDownloader/{filename}", "/JDownloader/JDownloader.jar"
                )
                break
        await rmtree("/JDownloader/update")
        await rmtree("/JDownloader/tmp")

    async def _wait_for_api(self, proc):
        LOGGER.info(f"🔄 JDownloader started (PID {proc.pid}), waiting for API...")
        max_wait = 45
        check_interval = 3
        
        for attempt in range(max_wait // check_interval):
            await asyncio.sleep(check_interval)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', 3128))
                sock.close()
                
                if result == 0:
                    wait_time = (attempt + 1) * check_interval
                    LOGGER.info(f"✅ JDownloader API ready on port 3128 after {wait_time}s")
                    return True
                else:
                    if attempt % 3 == 0:
                        elapsed = (attempt + 1) * check_interval
                        LOGGER.info(f"⏳ Waiting for API ({elapsed}s)")
            except Exception as sock_err:
                LOGGER.debug(f"Port check: {sock_err}")
        return False

    async def boot(self):
        """Boot JDownloader with proper credential checking"""
        await cmd_exec(["pkill", "-9", "-f", "java"], shell=False)
        
        jd_email, jd_pass = self._validate_jd_credentials()
        if not jd_email:
            return
        
        self.error = "Connecting... Try again after couple of seconds"
        device_name = self._get_device_name()
        await self._log_startup_message()
        await self._create_config_files(jd_email, jd_pass, device_name)
        await self._prepare_jar_file()
        
        cmd = ["java", "-Dsun.jnu.encoding=UTF-8", "-Dfile.encoding=UTF-8", "-Djava.awt.headless=true", "-jar", "/JDownloader/JDownloader.jar"]
        
        try:
            LOGGER.info("🚀 Launching JDownloader Java process in background...")
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=DEVNULL,
                stdout=DEVNULL,
                stderr=DEVNULL,
                start_new_session=True
            )
            
            api_ready = await self._wait_for_api(proc)
            
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

    @staticmethod
    def _write_json_file(file_path: str, data: dict):
        """Write JSON data to file (blocking)."""
        with open(file_path, "w") as handle:
            handle.truncate(0)
            dump(data, handle)


jdownloader = JDownloader()
