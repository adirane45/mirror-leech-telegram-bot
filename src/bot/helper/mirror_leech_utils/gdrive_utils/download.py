from io import FileIO
from logging import getLogger
from os import makedirs
from os import path as ospath

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from tenacity import RetryError, retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from ...ext_utils.bot_utils import SetInterval, async_to_sync
from ...mirror_leech_utils.gdrive_utils.helper import GoogleDriveHelper

LOGGER = getLogger(__name__)


class GoogleDriveDownload(GoogleDriveHelper):
    def __init__(self, listener, path):
        self.listener = listener
        self._updater = None
        self._path = path
        super().__init__()
        self.is_downloading = True

    def download(self):
        file_id = self.get_id_from_url(self.listener.link, self.listener.user_id)
        self.service = self.authorize()
        self._updater = SetInterval(self.update_interval, self.progress)
        try:
            meta = self.get_file_metadata(file_id)
            if meta.get("mimeType") == self.G_DRIVE_DIR_MIME_TYPE:
                self._download_folder(file_id, self._path, self.listener.name)
            else:
                makedirs(self._path, exist_ok=True)
                self._download_file(
                    file_id, self._path, self.listener.name, meta.get("mimeType")
                )
        except Exception as err:
            if isinstance(err, RetryError):
                LOGGER.info(f"Total Attempts: {err.last_attempt.attempt_number}")
                err = err.last_attempt.exception()
            err = str(err).replace(">", "").replace("<", "")
            if "downloadQuotaExceeded" in err:
                err = "Download Quota Exceeded."
            elif "File not found" in err:
                if not self.alt_auth and self.use_sa:
                    self.alt_auth = True
                    self.use_sa = False
                    LOGGER.error("File not found. Trying with token.pickle...")
                    self._updater.cancel()
                    return self.download()
                err = "File not found!"
            async_to_sync(self.listener.on_download_error, err)
            self.listener.is_cancelled = True
        finally:
            self._updater.cancel()
            if self.listener.is_cancelled:
                return
            async_to_sync(self.listener.on_download_complete)
            return

    def _ensure_local_folder_path(self, path, folder_name):
        folder_name = folder_name.replace("/", "")
        folder_path = f"{path}/{folder_name}"
        if not ospath.exists(folder_path):
            makedirs(folder_path)
        return folder_path

    def _resolve_item_target(self, item):
        file_id = item["id"]
        shortcut_details = item.get("shortcutDetails")
        if shortcut_details is not None:
            return shortcut_details["targetId"], shortcut_details["targetMimeType"]
        return file_id, item.get("mimeType")

    def _is_included_extension(self, filename):
        return filename.strip().lower().endswith(tuple(self.listener.included_extensions))

    def _is_excluded_extension(self, filename):
        return filename.strip().lower().endswith(tuple(self.listener.excluded_extensions))

    def _should_skip_file_download(self, path, filename):
        if ospath.isfile(f"{path}/{filename}"):
            return True
        if self.listener.included_extensions:
            return not self._is_included_extension(filename)
        return self._is_excluded_extension(filename)

    def _download_folder(self, folder_id, path, folder_name):
        path = self._ensure_local_folder_path(path, folder_name)
        result = self.get_files_by_folder_id(folder_id)
        if len(result) == 0:
            return

        result = sorted(result, key=lambda k: k["name"])
        for item in result:
            file_id, mime_type = self._resolve_item_target(item)
            filename = item["name"]

            if mime_type == self.G_DRIVE_DIR_MIME_TYPE:
                self._download_folder(file_id, path, filename)
            elif self._should_skip_file_download(path, filename):
                continue
            else:
                self._download_file(file_id, path, filename, mime_type)

            if self.listener.is_cancelled:
                break

    @retry(
        wait=wait_exponential(multiplier=2, min=3, max=6),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
    )
    def _download_file(self, file_id, path, filename, mime_type, export=False):
        request = self._create_download_request(file_id, export)
        filename = self._prepare_filename(filename, export)
        
        if len(filename.encode()) > 255:
            filename = self._truncate_filename(filename)
        
        if self.listener.is_cancelled:
            return
        
        fh = FileIO(f"{path}/{filename}", "wb")
        downloader = MediaIoBaseDownload(fh, request, chunksize=100 * 1024 * 1024)
        
        done = self._perform_download(downloader, fh, file_id, path, filename, mime_type)
        if done:
            self.file_processed_bytes = 0

    def _create_download_request(self, file_id, export):
        if export:
            return self.service.files().export_media(
                fileId=file_id, mimeType="application/pdf"
            )
        else:
            return self.service.files().get_media(
                fileId=file_id, supportsAllDrives=True, acknowledgeAbuse=True
            )

    def _prepare_filename(self, filename, export):
        filename = filename.replace("/", "")
        if export:
            filename = f"{filename}.pdf"
        return filename

    def _truncate_filename(self, filename):
        ext = ospath.splitext(filename)[1]
        filename = f"{filename[:245]}{ext}"
        if self.listener.name.strip().endswith(ext):
            self.listener.name = filename
        return filename

    def _perform_download(self, downloader, fh, file_id, path, filename, mime_type):
        done = False
        retries = 0
        while not done:
            if self.listener.is_cancelled:
                fh.close()
                break
            try:
                self.status, done = downloader.next_chunk()
            except HttpError as err:
                LOGGER.error(err)
                result = self._handle_download_error(
                    err, retries, file_id, path, filename, mime_type
                )
                if result is None:
                    return False
                if result is True:
                    retries += 1
                    continue
                return result
        return done

    def _handle_download_error(self, err, retries, file_id, path, filename, mime_type):
        if err.resp.status in [500, 502, 503, 504, 429] and retries < 10:
            return True
        
        if not err.resp.get("content-type", "").startswith("application/json"):
            raise err
        
        reason = eval(err.content).get("error").get("errors")[0].get("reason")
        
        if "fileNotDownloadable" in reason and "document" in mime_type:
            return self._download_file(file_id, path, filename, mime_type, True)
        
        if reason not in ["downloadQuotaExceeded", "dailyLimitExceeded"]:
            raise err
        
        if self.use_sa:
            return self._try_service_account_switch(reason, file_id, path, filename, mime_type)
        else:
            LOGGER.error(f"Got: {reason}")
            raise err

    def _try_service_account_switch(self, reason, file_id, path, filename, mime_type):
        if self.sa_count >= self.sa_number:
            LOGGER.info(
                f"Reached maximum number of service accounts switching, which is {self.sa_count}"
            )
            raise HttpError(None, b'')
        if self.listener.is_cancelled:
            return None
        self.switch_service_account()
        LOGGER.info(f"Got: {reason}, Trying Again...")
        return self._download_file(file_id, path, filename, mime_type)
