from .core_admin import register_core_admin_handlers
from .media_archive import register_media_archive_handlers
from .mirror_leech import register_mirror_leech_handlers
from .optional_features import register_optional_features
from .queue_controls import register_queue_control_handlers
from .status_dashboard import (
	register_status_dashboard_handlers,
	register_task_status_handlers,
)

__all__ = [
	"register_optional_features",
	"register_core_admin_handlers",
	"register_mirror_leech_handlers",
	"register_media_archive_handlers",
	"register_queue_control_handlers",
	"register_task_status_handlers",
	"register_status_dashboard_handlers",
]
