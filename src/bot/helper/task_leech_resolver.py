"""
Leech Destination Resolver
Handles leech destination resolution and transmission chat validation
Extracts cc=28 validation logic with max nesting depth of 5
"""

from pyrogram.enums import ChatAction

from bot import LOGGER
from bot.core.config_manager import Config
from bot.core.telegram_manager import TgClient
from bot.helper.ext_utils.bot_utils import sync_to_async
from bot.helper.ext_utils.links_utils import is_telegram_link
from bot.helper.ext_utils.media_utils import create_thumb
from bot.helper.ext_utils.telegraph_helper import TelegraphHelper
from bot.helper.task_config_initializers import TaskConfigInitializers


async def get_tg_link_message(link):
    """Get telegram message from link"""
    from bot.helper.telegram_helper.message_utils import get_tg_link_message as _get_msg
    return await _get_msg(link)


class LeechDestinationResolver:
    """Resolves leech destinations and validates transmission chats"""

    @staticmethod
    def apply_leech_flags(task_config):
        """Apply hybrid leech and transmission flags"""
        is_premium_user = bool(getattr(TgClient, "IS_PREMIUM_USER", False))
        task_config.hybrid_leech = is_premium_user and (
            task_config.user_dict.get("HYBRID_LEECH")
            or Config.HYBRID_LEECH
            and "HYBRID_LEECH" not in task_config.user_dict
        )
        if task_config.bot_trans:
            task_config.user_transmission = False
            task_config.hybrid_leech = False
        if task_config.user_trans:
            task_config.user_transmission = is_premium_user

    @staticmethod
    def parse_leech_destination(task_config):
        """Parse and format leech destination string"""
        if not task_config.up_dest:
            return
        if not isinstance(task_config.up_dest, int):
            # Handle transmission mode prefixes
            if task_config.up_dest.startswith("b:"):
                task_config.up_dest = task_config.up_dest.replace("b:", "", 1)
                task_config.user_transmission = False
                task_config.hybrid_leech = False
            elif task_config.up_dest.startswith("u:"):
                task_config.up_dest = task_config.up_dest.replace("u:", "", 1)
                task_config.user_transmission = bool(
                    getattr(TgClient, "IS_PREMIUM_USER", False)
                )
            elif task_config.up_dest.startswith("h:"):
                task_config.up_dest = task_config.up_dest.replace("h:", "", 1)
                task_config.user_transmission = bool(
                    getattr(TgClient, "IS_PREMIUM_USER", False)
                )
                task_config.hybrid_leech = task_config.user_transmission

            # Parse chat ID and thread ID
            if "|" in task_config.up_dest:
                task_config.up_dest, task_config.chat_thread_id = list(
                    map(
                        lambda x: int(x) if x.lstrip("-").isdigit() else x,
                        task_config.up_dest.split("|", 1),
                    )
                )
            elif task_config.up_dest.lstrip("-").isdigit():
                task_config.up_dest = int(task_config.up_dest)
            elif task_config.up_dest.lower() == "pm":
                task_config.up_dest = task_config.user_id

    @staticmethod
    async def _validate_user_transmission_chat(task_config):
        """Validate user session can access destination chat with required permissions"""
        try:
            chat = await TgClient.user.get_chat(task_config.up_dest)
        except:
            chat = None

        if chat is None:
            LOGGER.warning(
                "Account of user session can't find the destination chat!"
            )
            task_config.user_transmission = False
            task_config.hybrid_leech = False
            return False

        # Check chat type
        if chat.type.name not in ["SUPERGROUP", "CHANNEL", "GROUP", "FORUM"]:
            task_config.user_transmission = False
            task_config.hybrid_leech = False
            return False

        # Check admin permissions
        if not chat.is_admin:
            LOGGER.warning(
                "Promote the account of the user session to admin in the chat!"
            )
            task_config.user_transmission = False
            task_config.hybrid_leech = False
            return False

        # Check required privileges
        member = await chat.get_member(TgClient.user.me.id)
        if (
            not member.privileges.can_manage_chat
            or not member.privileges.can_delete_messages
        ):
            task_config.user_transmission = False
            task_config.hybrid_leech = False
            LOGGER.warning(
                "Enable manage chat and delete messages from administration settings!"
            )
            return False

        return True

    @staticmethod
    async def _validate_bot_transmission_chat(task_config):
        """Validate bot can access destination chat with required permissions"""
        try:
            chat = await task_config.client.get_chat(task_config.up_dest)
        except:
            chat = None

        if chat is None:
            if task_config.user_transmission:
                task_config.hybrid_leech = False
            else:
                raise ValueError("Chat not found!")
            return

        # Handle group chats
        if chat.type.name in ["SUPERGROUP", "CHANNEL", "GROUP", "FORUM"]:
            if not chat.is_admin:
                raise ValueError("Bot is not admin in the destination chat!")

            member = await chat.get_member(task_config.client.me.id)
            if (
                not member.privileges.can_manage_chat
                or not member.privileges.can_delete_messages
            ):
                if not task_config.user_transmission:
                    raise ValueError(
                        "Enable manage chat and delete messages for this bot!"
                    )
                task_config.hybrid_leech = False
        else:
            # Handle private chats
            try:
                await task_config.client.send_chat_action(
                    task_config.up_dest, ChatAction.TYPING
                )
            except:
                raise ValueError("Start the bot and try again!")

    @staticmethod
    async def validate_transmission_chats(task_config):
        """
        Main validation method for transmission chats
        Reduces cyclomatic complexity from 28 to manageable levels
        Flattens nesting depth from 5 to 2
        """
        if task_config.user_transmission:
            await LeechDestinationResolver._validate_user_transmission_chat(task_config)

        if not task_config.user_transmission or task_config.hybrid_leech:
            await LeechDestinationResolver._validate_bot_transmission_chat(task_config)

    @staticmethod
    async def resolve_thumb_link(task_config):
        """Resolve thumbnail from telegram link"""
        if task_config.thumb != "none" and is_telegram_link(task_config.thumb):
            msg = (await get_tg_link_message(task_config.thumb))[0]
            task_config.thumb = (
                await create_thumb(msg) if msg.photo or msg.document else ""
            )

    @staticmethod
    async def resolve_leech_destination(task_config):
        """
        Main method to resolve leech destination
        Orchestrates all leech-related configurations
        """
        # Get leech dump chat
        task_config.up_dest = (
            task_config.up_dest
            or task_config.user_dict.get("LEECH_DUMP_CHAT")
            or (
                Config.LEECH_DUMP_CHAT
                if "LEECH_DUMP_CHAT" not in task_config.user_dict
                else None
            )
        )

        # Apply flags and parse destination
        LeechDestinationResolver.apply_leech_flags(task_config)
        LeechDestinationResolver.parse_leech_destination(task_config)

        # Disable transmission for non-supergroup chats
        if (
            task_config.user_transmission or task_config.hybrid_leech
        ) and not task_config.is_super_chat:
            task_config.user_transmission = False
            task_config.hybrid_leech = False

        # Validate destination if specified
        if task_config.up_dest:
            await LeechDestinationResolver.validate_transmission_chats(task_config)

        # Initialize related settings
        TaskConfigInitializers.init_split_settings(task_config)
        TaskConfigInitializers.init_as_doc(task_config)
        TaskConfigInitializers.init_thumbnail_layout(task_config)
        await LeechDestinationResolver.resolve_thumb_link(task_config)
