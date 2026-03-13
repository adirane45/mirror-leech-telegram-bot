from logging import getLogger

from .... import drives_ids, drives_names, index_urls, user_data
from ....helper.ext_utils.status_utils import get_readable_file_size
from ....helper.mirror_leech_utils.gdrive_utils.helper import GoogleDriveHelper

LOGGER = getLogger(__name__)


class GoogleDriveSearch(GoogleDriveHelper):

    def __init__(self, stop_dup=False, no_multi=False, is_recursive=True, item_type=""):
        super().__init__()
        self._stop_dup = stop_dup
        self._no_multi = no_multi
        self._is_recursive = is_recursive
        self._item_type = item_type

    def _build_name_contains_clause(self, file_name):
        names = file_name.split()
        return "".join(
            f"name contains '{name}' and "
            for name in names
            if name != ""
        )

    def _build_parent_clause(self, is_recursive, dir_id):
        if is_recursive:
            return ""
        return f"'{dir_id}' in parents and "

    def _build_name_clause(self, file_name, is_recursive):
        if self._stop_dup:
            return f"name = '{file_name}' and "
        return self._build_name_contains_clause(file_name)

    def _build_type_clause(self):
        if self._item_type == "files":
            return f"mimeType != '{self.G_DRIVE_DIR_MIME_TYPE}' and "
        if self._item_type == "folders":
            return f"mimeType = '{self.G_DRIVE_DIR_MIME_TYPE}' and "
        return ""

    def _build_query_string(self, file_name, is_recursive, dir_id):
        """Build query string based on search parameters"""
        query = self._build_parent_clause(is_recursive, dir_id)
        query += self._build_name_clause(file_name, is_recursive)
        if not self._stop_dup:
            query += self._build_type_clause()
        query += "trashed = false"
        return query
    
    def _execute_recursive_root_query(self, query):
        """Execute query for recursive search in root"""
        return (
            self.service.files()
            .list(
                q=f"{query} and 'me' in owners",
                pageSize=200,
                spaces="drive",
                fields="files(id, name, mimeType, size, parents)",
                orderBy="folder, name asc",
            )
            .execute()
        )
    
    def _execute_recursive_drive_query(self, query, dir_id):
        """Execute query for recursive search in drive"""
        return (
            self.service.files()
            .list(
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                driveId=dir_id,
                q=query,
                spaces="drive",
                pageSize=150,
                fields="files(id, name, mimeType, size, teamDriveId, parents)",
                corpora="drive",
                orderBy="folder, name asc",
            )
            .execute()
        )
    
    def _execute_non_recursive_query(self, query):
        """Execute query for non-recursive search"""
        return (
            self.service.files()
            .list(
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                q=query,
                spaces="drive",
                pageSize=150,
                fields="files(id, name, mimeType, size)",
                orderBy="folder, name asc",
            )
            .execute()
        )
    
    def _drive_query(self, dir_id, file_name, is_recursive):
        try:
            query = self._build_query_string(file_name, is_recursive, dir_id)
            
            if is_recursive:
                if dir_id == "root":
                    return self._execute_recursive_root_query(query)
                else:
                    return self._execute_recursive_drive_query(query, dir_id)
            else:
                return self._execute_non_recursive_query(query)
        except Exception as err:
            err = str(err).replace(">", "").replace("<", "")
            LOGGER.error(err)
            return {"files": []}

    def _prepare_drives(self, target_id, user_id):
        """Prepare drives list based on target_id."""
        if target_id.startswith("mtp:"):
            return self.get_user_drive(target_id, user_id)
        if target_id:
            return [
                (
                    "From Owner",
                    target_id.replace("tp:", "", 1),
                    index_urls[0] if index_urls else "",
                )
            ]
        return zip(drives_names, drives_ids, index_urls)

    def _should_use_sa(self, target_id):
        """Determine if service accounts should be used."""
        return not (
            target_id.startswith("mtp:")
            or (not target_id.startswith("mtp:") and len(drives_ids) > 1)
            or target_id.startswith("tp:")
        )

    def _build_folder_message(self, file, index_url):
        """Build message for folder item."""
        furl = self.G_DRIVE_DIR_BASE_DOWNLOAD_URL.format(file.get("id"))
        msg = f"📁 <code>{file.get('name')}<br>(folder)</code><br>"
        msg += f"<b><a href={furl}>Drive Link</a></b>"
        if index_url:
            url = f'{index_url}findpath?id={file.get("id")}'
            msg += f' <b>| <a href="{url}">Index Link</a></b>'
        return msg

    def _build_shortcut_message(self, file):
        """Build message for shortcut item."""
        furl = self.G_DRIVE_DIR_BASE_DOWNLOAD_URL.format(file.get("id"))
        return (
            f"⁍<a href='{furl}'>{file.get('name')}"
            f"</a> (shortcut)"
        )

    def _build_file_message(self, file, index_url, mime_type):
        """Build message for file item."""
        furl = self.G_DRIVE_BASE_DOWNLOAD_URL.format(file.get("id"))
        msg = f"📄 <code>{file.get('name')}<br>({get_readable_file_size(int(file.get('size', 0)))})</code><br>"
        msg += f"<b><a href={furl}>Drive Link</a></b>"
        if index_url:
            url = f'{index_url}findpath?id={file.get("id")}'
            msg += f' <b>| <a href="{url}">Index Link</a></b>'
            if mime_type.startswith(("image", "video", "audio")):
                urlv = f'{index_url}findpath?id={file.get("id")}&view=true'
                msg += f' <b>| <a href="{urlv}">View Link</a></b>'
        return msg

    def _build_file_item_message(self, file, index_url):
        """Build message for a file item based on its MIME type."""
        mime_type = file.get("mimeType")
        if mime_type == self.G_DRIVE_DIR_MIME_TYPE:
            return self._build_folder_message(file, index_url)
        if mime_type == "application/vnd.google-apps.shortcut":
            return self._build_shortcut_message(file)
        return self._build_file_message(file, index_url, mime_type)

    def _calculate_recursive_flag(self, dir_id):
        return False if self._is_recursive and len(dir_id) > 23 else self._is_recursive

    def _append_drive_header(self, msg, drive_name):
        if drive_name:
            msg += f"╾────────────╼<br><b>{drive_name}</b><br>╾────────────╼<br>"
        return msg

    def _append_drive_files(self, msg, response_files, index_url, telegraph_content, contents_no):
        for file in response_files:
            msg += self._build_file_item_message(file, index_url)
            msg += "<br><br>"
            contents_no += 1
            if len(msg.encode("utf-8")) > 39000:
                telegraph_content.append(msg)
                msg = ""
        return msg, contents_no

    def _should_skip_drive(self, response_files):
        return not response_files and not self._no_multi

    def _should_stop_after_drive(self, response_files):
        return not response_files and self._no_multi

    def drive_list(self, file_name, target_id="", user_id=""):
        msg = ""
        file_name = self.escapes(str(file_name))
        contents_no = 0
        telegraph_content = []
        Title = False

        drives = self._prepare_drives(target_id, user_id)
        self.use_sa = self._should_use_sa(target_id)
        self.service = self.authorize()

        for drive_name, dir_id, index_url in drives:
            isRecur = self._calculate_recursive_flag(dir_id)
            response = self._drive_query(dir_id, file_name, isRecur)
            response_files = response.get("files", [])

            if self._should_stop_after_drive(response_files):
                break
            if self._should_skip_drive(response_files):
                continue

            if not Title:
                msg += f"<h4>Search Result For {file_name}</h4>"
                Title = True
            msg = self._append_drive_header(msg, drive_name)
            msg, contents_no = self._append_drive_files(
                msg,
                response_files,
                index_url,
                telegraph_content,
                contents_no,
            )

            if self._no_multi:
                break

        if msg != "":
            telegraph_content.append(msg)

        return telegraph_content, contents_no

    def get_user_drive(self, target_id, user_id):
        dest_id = target_id.replace("mtp:", "", 1)
        self.token_path = f"tokens/{user_id}.pickle"
        self.use_sa = False
        user_dict = user_data.get(user_id, {})
        INDEX = user_dict["index_url"] if user_dict.get("index_url") else ""
        return [("User Choice", dest_id, INDEX)]
