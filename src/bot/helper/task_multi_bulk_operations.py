"""
Multi and Bulk Task Operations
Handles multi-task and bulk download operations
"""

from asyncio import sleep
from secrets import token_urlsafe

from bot import intervals, multi_tags, task_dict_lock, user_data
from bot.helper.ext_utils.bot_utils import new_task
from bot.helper.ext_utils.bulk_links import extract_bulk_links
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import send_message, send_status_message


class MultiTaskOperations:
    """Handles multi-task and bulk operations"""

    @staticmethod
    def _set_tag_from_user(task_config):
        if not task_config.user:
            return
        if username := task_config.user.username:
            task_config.tag = f"@{username}"
        elif hasattr(task_config.user, "mention"):
            task_config.tag = task_config.user.mention
        else:
            task_config.tag = task_config.user.title

    @staticmethod
    def _parse_rss_tag_info(text: list, task_config):
        user_info = text[1].split("Tag: ")
        if len(user_info) >= 3:
            task_config.tag = " ".join(user_info[:-1])
            return user_info[-1]
        task_config.tag, id_ = text[1].split("Tag: ")[1].split()
        return id_

    @staticmethod
    async def _load_rss_user(task_config, user_id):
        task_config.user = task_config.message.from_user = (
            await task_config.client.get_users(int(user_id))
        )
        task_config.user_id = task_config.user.id
        task_config.user_dict = user_data.get(task_config.user_id, {})
        try:
            await task_config.message.unpin()
        except:
            pass

    @staticmethod
    async def get_tag(task_config, text: list):
        """Parse and set user tag from message"""
        if len(text) <= 1 or not text[1].startswith("Tag: "):
            MultiTaskOperations._set_tag_from_user(task_config)
            return

        task_config.is_rss = True
        id_ = MultiTaskOperations._parse_rss_tag_info(text, task_config)
        await MultiTaskOperations._load_rss_user(task_config, id_)
        MultiTaskOperations._set_tag_from_user(task_config)

    @staticmethod
    def _setup_multi_tag(task_config):
        """Setup multi-task tag"""
        if not task_config.multi_tag and task_config.multi > 1:
            task_config.multi_tag = token_urlsafe(3)
            multi_tags.add(task_config.multi_tag)
            return True
        elif task_config.multi <= 1:
            if task_config.multi_tag in multi_tags:
                multi_tags.discard(task_config.multi_tag)
            return False
        return True

    @staticmethod
    async def _check_multi_cancelled(task_config):
        """Check if multi-task was cancelled"""
        if task_config.multi_tag and task_config.multi_tag not in multi_tags:
            await send_message(
                task_config.message, f"{task_config.tag} Multi Task has been cancelled!"
            )
            await send_status_message(task_config.message)
            async with task_dict_lock:
                for fd_name in task_config.same_dir:
                    task_config.same_dir[fd_name]["total"] -= task_config.multi
            return True
        return False

    @staticmethod
    def _build_multi_message(task_config, input_list):
        """Build message for next multi-task iteration"""
        if len(task_config.bulk) != 0:
            msg = input_list[:1]
            msg.append(
                f"{task_config.bulk[0]} -i {task_config.multi - 1} {task_config.options}"
            )
            msgts = " ".join(msg)
        else:
            msg = [s.strip() for s in input_list]
            index = msg.index("-i")
            msg[index + 1] = f"{task_config.multi - 1}"
            msgts = " ".join(msg)

        if task_config.multi > 2:
            msgts += f"\nCancel Multi: <code>/{BotCommands.CancelTaskCommand[1]} {task_config.multi_tag}</code>"
        return msgts

    @staticmethod
    @new_task
    async def run_multi(task_config, input_list, obj):
        """Execute multi-task operation"""
        await sleep(7)

        # Setup multi tag
        if not MultiTaskOperations._setup_multi_tag(task_config):
            return

        # Check if cancelled
        if await MultiTaskOperations._check_multi_cancelled(task_config):
            return

        # Build and send message
        msgts = MultiTaskOperations._build_multi_message(task_config, input_list)

        if len(task_config.bulk) != 0:
            nextmsg = await send_message(task_config.message, msgts)
        else:
            nextmsg = await task_config.client.get_messages(
                chat_id=task_config.message.chat.id,
                message_ids=task_config.message.reply_to_message_id + 1,
            )
            nextmsg = await send_message(nextmsg, msgts)

        nextmsg = await task_config.client.get_messages(
            chat_id=task_config.message.chat.id, message_ids=nextmsg.id
        )

        if task_config.message.from_user:
            nextmsg.from_user = task_config.user
        else:
            nextmsg.sender_chat = task_config.user

        if intervals["stopAll"]:
            return

        await obj(
            task_config.client,
            nextmsg,
            task_config.is_qbit,
            task_config.is_leech,
            task_config.is_jd,
            task_config.is_nzb,
            task_config.same_dir,
            task_config.bulk,
            task_config.multi_tag,
            task_config.options,
        ).new_event()


class BulkTaskOperations:
    """Handles bulk download operations"""

    @staticmethod
    def build_bulk_message(task_config, input_list, bulk_start, bulk_end):
        """Build message for bulk operation"""
        b_msg = input_list[:1]
        task_config.options = input_list[1:]
        index = task_config.options.index("-b")
        del task_config.options[index]
        if bulk_start or bulk_end:
            del task_config.options[index]
        task_config.options = " ".join(task_config.options)
        b_msg.append(
            f"{task_config.bulk[0]} -i {len(task_config.bulk)} {task_config.options}"
        )
        msg = " ".join(b_msg)
        if len(task_config.bulk) > 2:
            task_config.multi_tag = token_urlsafe(3)
            multi_tags.add(task_config.multi_tag)
            msg += f"\nCancel Multi: <code>/{BotCommands.CancelTaskCommand[1]} {task_config.multi_tag}</code>"
        return msg

    @staticmethod
    async def init_bulk(task_config, input_list, bulk_start, bulk_end, obj):
        """Initialize bulk download operation"""
        try:
            task_config.bulk = await extract_bulk_links(
                task_config.message, bulk_start, bulk_end
            )
            if len(task_config.bulk) == 0:
                raise ValueError("Bulk Empty!")

            msg = BulkTaskOperations.build_bulk_message(
                task_config, input_list, bulk_start, bulk_end
            )
            nextmsg = await send_message(task_config.message, msg)
            nextmsg = await task_config.client.get_messages(
                chat_id=task_config.message.chat.id, message_ids=nextmsg.id
            )

            if task_config.message.from_user:
                nextmsg.from_user = task_config.user
            else:
                nextmsg.sender_chat = task_config.user

            await obj(
                task_config.client,
                nextmsg,
                task_config.is_qbit,
                task_config.is_leech,
                task_config.is_jd,
                task_config.is_nzb,
                task_config.same_dir,
                task_config.bulk,
                task_config.multi_tag,
                task_config.options,
            ).new_event()
        except Exception as e:
            await send_message(
                task_config.message,
                f"Reply to text file or to telegram message that have links separated by new line! {e}",
            )
