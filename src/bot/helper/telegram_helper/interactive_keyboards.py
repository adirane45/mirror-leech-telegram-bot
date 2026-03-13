# Enhanced Interactive Keyboards for Better UI/UX
# Modified by: justadi

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class InteractiveKeyboards:
    """
    Provides interactive keyboard buttons for various bot operations.
    Enhances user experience with quick action buttons.
    Modified by: justadi
    """

    @staticmethod
    def task_actions(gid: str):
        """Quick action buttons for a task"""
        buttons = [
            [
                InlineKeyboardButton("⏸️ Pause", callback_data=f"pause_{gid}"),
                InlineKeyboardButton("⏹️ Cancel", callback_data=f"cancel_{gid}"),
            ],
            [
                InlineKeyboardButton("🔍 Details", callback_data=f"details_{gid}"),
                InlineKeyboardButton("↗️ Speed", callback_data=f"speed_{gid}"),
            ],
            [
                InlineKeyboardButton("⬆️ Priority", callback_data=f"priority_{gid}"),
                InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_{gid}"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def queue_management():
        """Buttons for queue management dashboard"""
        buttons = [
            [
                InlineKeyboardButton("📋 Active", callback_data="queue_active"),
                InlineKeyboardButton("⏸️ Paused", callback_data="queue_paused"),
            ],
            [
                InlineKeyboardButton("⏳ Queued", callback_data="queue_queued"),
                InlineKeyboardButton("✅ Completed", callback_data="queue_completed"),
            ],
            [
                InlineKeyboardButton("⏸️ Pause All", callback_data="pauseall_confirm"),
                InlineKeyboardButton("▶️ Resume All", callback_data="resumeall_confirm"),
            ],
            [InlineKeyboardButton("❌ Close", callback_data="queue_close")],
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def priority_selector(gid: str):
        """Priority level selector"""
        buttons = [
            [
                InlineKeyboardButton("⬇️ Low (-1)", callback_data=f"set_pri_{gid}_-1"),
                InlineKeyboardButton("➡️ Normal (0)", callback_data=f"set_pri_{gid}_0"),
                InlineKeyboardButton("⬆️ High (1)", callback_data=f"set_pri_{gid}_1"),
            ],
            [InlineKeyboardButton("« Back", callback_data=f"task_menu_{gid}")],
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def task_confirmation(action: str, gid: str):
        """Confirmation dialog for important actions"""
        action_text = {
            "cancel": "❌ Cancel Task?",
            "pause": "⏸️ Pause Task?",
            "resume": "▶️ Resume Task?",
        }.get(action, "Confirm Action?")

        buttons = [
            [
                InlineKeyboardButton("✅ Yes", callback_data=f"confirm_{action}_{gid}"),
                InlineKeyboardButton("❌ No", callback_data=f"cancel_confirm_{gid}"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def status_filter():
        """Filter buttons for status view"""
        buttons = [
            [
                InlineKeyboardButton("▶️ Running", callback_data="status_running"),
                InlineKeyboardButton("⏸️ Paused", callback_data="status_paused"),
            ],
            [
                InlineKeyboardButton("⏳ Queued", callback_data="status_queued"),
                InlineKeyboardButton("❌ Failed", callback_data="status_failed"),
            ],
            [InlineKeyboardButton("📊 All Tasks", callback_data="status_all")],
            [InlineKeyboardButton("❌ Close", callback_data="status_close")],
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def search_filter():
        """Filter buttons for search/download history"""
        buttons = [
            [
                InlineKeyboardButton("🔍 By Name", callback_data="search_name"),
                InlineKeyboardButton("🆔 By GID", callback_data="search_gid"),
            ],
            [
                InlineKeyboardButton("📅 By Date", callback_data="search_date"),
                InlineKeyboardButton("📊 Statistics", callback_data="search_stats"),
            ],
            [InlineKeyboardButton("❌ Close", callback_data="search_close")],
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def pagination(current_page: int, total_pages: int, prefix: str):
        """Pagination buttons for long lists"""
        buttons = []

        # Navigation row
        nav_buttons = []
        if current_page > 0:
            nav_buttons.append(
                InlineKeyboardButton("⬅️ Prev", callback_data=f"{prefix}_page_{current_page - 1}")
            )
        nav_buttons.append(
            InlineKeyboardButton(
                f"📄 {current_page + 1}/{total_pages}",
                callback_data=f"{prefix}_page_info",
            )
        )
        if current_page < total_pages - 1:
            nav_buttons.append(
                InlineKeyboardButton("Next ➡️", callback_data=f"{prefix}_page_{current_page + 1}")
            )
        buttons.append(nav_buttons)

        # Close button
        buttons.append([InlineKeyboardButton("❌ Close", callback_data=f"{prefix}_close")])

        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def task_menu(gid: str):
        """Main task menu with all options"""
        buttons = [
            [
                InlineKeyboardButton("⏸️ Pause", callback_data=f"pause_confirm_{gid}"),
                InlineKeyboardButton("⏹️ Cancel", callback_data=f"cancel_confirm_{gid}"),
            ],
            [
                InlineKeyboardButton("⬆️ Priority", callback_data=f"priority_{gid}"),
                InlineKeyboardButton("🔍 Details", callback_data=f"details_{gid}"),
            ],
            [
                InlineKeyboardButton("📊 Stats", callback_data=f"stats_{gid}"),
                InlineKeyboardButton("🔗 Link", callback_data=f"link_{gid}"),
            ],
            [InlineKeyboardButton("« Back", callback_data="queue_back")],
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def quick_actions():
        """Quick action buttons for main dashboard"""
        buttons = [
            [
                InlineKeyboardButton("📋 Queue", callback_data="quick_queue"),
                InlineKeyboardButton("📊 Status", callback_data="quick_status"),
            ],
            [
                InlineKeyboardButton("📈 Stats", callback_data="quick_stats"),
                InlineKeyboardButton("🚀 Speed", callback_data="quick_speed"),
            ],
            [
                InlineKeyboardButton("🔍 Search", callback_data="quick_search"),
                InlineKeyboardButton("⚙️ Settings", callback_data="quick_settings"),
            ],
        ]
        return InlineKeyboardMarkup(buttons)

    @staticmethod
    def toggle_buttons(options: dict, prefix: str):
        """Generic toggle/selection buttons"""
        buttons = []
        for option, data in options.items():
            buttons.append(
                [InlineKeyboardButton(option, callback_data=f"{prefix}_{data}")]
            )
        buttons.append([InlineKeyboardButton("❌ Close", callback_data=f"{prefix}_close")])
        return InlineKeyboardMarkup(buttons)
