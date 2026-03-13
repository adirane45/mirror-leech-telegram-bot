from anytree import NodeMixin
from typing import Any, Iterable


class TorNode(NodeMixin):  # type: ignore[misc]
    def __init__(
        self,
        name: str,
        is_folder: bool = False,
        is_file: bool = False,
        parent: "TorNode | None" = None,
        size: int | float | None = None,
        priority: int | None = None,
        file_id: int | str | None = None,
        progress: float | int | None = None,
    ) -> None:
        super().__init__()
        self.name = name
        self.is_folder = is_folder
        self.is_file = is_file

        if parent is not None:
            self.parent = parent
        if size is not None:
            self.fsize = size
        if priority is not None:
            self.priority = priority
        if file_id is not None:
            self.file_id = file_id
        if progress is not None:
            self.progress = progress


def qb_get_folders(path: str) -> list[str]:
    return path.split("/")


def get_folders(path: str, root_path: str) -> list[str]:
    fs = path.split(root_path)[-1]
    return fs.split("/")


def _build_folder_tree(folders, parent, folder_id):
    """Build folder tree structure from folder path list"""
    previous_node = parent
    for j in range(len(folders) - 1):
        current_node = next(
            (k for k in previous_node.children if k.name == folders[j]),
            None,
        )
        if current_node is None:
            previous_node = TorNode(
                folders[j],
                is_folder=True,
                parent=previous_node,
                file_id=folder_id[0],
            )
            folder_id[0] += 1
        else:
            previous_node = current_node
    return previous_node

def _make_qbittorrent_tree(res):
    """Create tree structure for qBittorrent files"""
    parent = TorNode("QBITTORRENT")
    folder_id = [0]
    for i in res:
        folders = qb_get_folders(i.name)
        if len(folders) > 1:
            previous_node = _build_folder_tree(folders, parent, folder_id)
        else:
            previous_node = parent
        TorNode(
            folders[-1],
            is_file=True,
            parent=previous_node,
            size=i.size,
            priority=i.priority,
            file_id=i.index,
            progress=round(i.progress * 100, 5),
        )
    return parent

def _calculate_aria2_progress(file_info):
    """Calculate progress for aria2 file"""
    try:
        return round(
            (int(file_info["completedLength"]) / int(file_info["length"])) * 100, 5
        )
    except (TypeError, ValueError, ZeroDivisionError):
        return 0

def _make_aria2_tree(res, root_path):
    """Create tree structure for aria2 files"""
    parent = TorNode("ARIA2")
    folder_id = [0]
    for i in res:
        folders = get_folders(i["path"], root_path)
        priority = 1 if i["selected"] != "false" else 0
        
        if len(folders) > 1:
            previous_node = _build_folder_tree(folders, parent, folder_id)
        else:
            previous_node = parent
        
        progress = _calculate_aria2_progress(i)
        TorNode(
            folders[-1],
            is_file=True,
            parent=previous_node,
            size=int(i["length"]),
            priority=priority,
            file_id=i["index"],
            progress=progress,
        )
    return parent

def _make_sabnzbd_tree(res):
    """Create tree structure for SABnzbd files"""
    parent = TorNode("SABNZBD+")
    priority = 1
    for i in res["files"]:
        TorNode(
            i["filename"],
            is_file=True,
            parent=parent,
            size=float(i["mb"]) * 1048576,
            priority=priority,
            file_id=i["nzf_id"],
            progress=round(
                ((float(i["mb"]) - float(i["mbleft"])) / float(i["mb"])) * 100,
                5,
            ),
        )
    return parent

def make_tree(res: Any, tool: str, root_path: str = "") -> dict[str, Any]:
    if tool == "qbittorrent":
        parent = _make_qbittorrent_tree(res)
    elif tool == "aria2":
        parent = _make_aria2_tree(res, root_path)
    else:
        parent = _make_sabnzbd_tree(res)
    
    result = create_list(parent)
    return {"files": result, "engine": tool}


"""
def print_tree(parent):
    for pre, _, node in RenderTree(parent):
        treestr = u"%s%s" % (pre, node.name)
        print(treestr.ljust(8), node.is_folder, node.is_file)
"""


def create_list(
    parent: TorNode, contents: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    if contents is None:
        contents = []
    for i in parent.children:
        if i.is_folder:
            children: list[dict[str, Any]] = []
            create_list(i, children)
            contents.append(
                {
                    "id": f"folderNode_{i.file_id}",
                    "name": i.name,
                    "type": "folder",
                    "children": children,
                }
            )
        else:
            contents.append(
                {
                    "id": i.file_id,
                    "name": i.name,
                    "size": i.fsize,
                    "type": "file",
                    "selected": bool(i.priority),
                    "progress": i.progress,
                }
            )
    return contents


def extract_file_ids(data: Iterable[dict[str, Any]]) -> tuple[list[str], list[str]]:
    selected_files: list[str] = []
    unselected_files: list[str] = []
    for item in data:
        if item.get("type") == "file":
            if item.get("selected"):
                selected_files.append(str(item["id"]))
            else:
                unselected_files.append(str(item["id"]))
        if item.get("children"):
            child_selected, child_unselected = extract_file_ids(item["children"])
            selected_files.extend(child_selected)
            unselected_files.extend(child_unselected)
    return selected_files, unselected_files
