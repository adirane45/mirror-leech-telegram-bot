"""
GitOps Auto-Updater with Graceful Shutdown

Implements:
- Check for updates via Git
- Pull latest code
- Run migrations if needed
- Graceful shutdown and restart
- Rollback on failure
"""

import asyncio
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .. import LOGGER
from .config_manager import Config


class GitOpsUpdater:
    """Manage bot updates via GitOps"""

    def __init__(self):
        self.enabled = bool(getattr(Config, "ENABLE_AUTO_UPDATE", False))
        self.repo_path = getattr(Config, "REPO_PATH", ".")
        self.check_interval = int(getattr(Config, "UPDATE_CHECK_INTERVAL_HOURS", 24)) * 3600
        self.last_check: Optional[datetime] = None
        self.last_update: Optional[datetime] = None
        self.update_count = 0

    async def check_for_updates(self) -> bool:
        """Check if updates are available"""
        if not self.enabled:
            return False

        try:
            # Fetch from remote
            result = await self._run_git_command(["fetch", "origin"])
            if result != 0:
                LOGGER.warning("Git fetch failed")
                return False

            # Check if local is behind remote
            result = await self._run_git_command(
                ["log", "--oneline", "HEAD..origin/master", f"--pretty=format:%H"]
            )

            self.last_check = datetime.now(timezone.utc)
            return len(result.strip()) > 0

        except Exception as e:
            LOGGER.error(f"Failed to check for updates: {e}")
            return False

    async def apply_updates(self, restart_callback: Optional[callable] = None) -> bool:
        """Apply pending updates"""
        if not self.enabled:
            return False

        try:
            LOGGER.info("Applying updates...")

            # Save current state
            current_hash = await self._get_current_hash()

            # Pull latest
            result = await self._run_git_command(["pull", "origin", "master"])
            if result != 0:
                LOGGER.error("Git pull failed")
                await self._rollback(current_hash)
                return False

            # Run migrations if needed
            migration_script = os.path.join(self.repo_path, "scripts/db_update.sh")
            if await asyncio.to_thread(os.path.exists, migration_script):
                LOGGER.info("Running database migrations...")
                result = await self._run_command(["bash", migration_script])
                if result != 0:
                    LOGGER.error("Migration failed")
                    await self._rollback(current_hash)
                    return False

            # Run tests
            LOGGER.info("Running test suite...")
            result = await self._run_command(["python", "-m", "pytest", "tests/", "-q"])
            if result != 0:
                LOGGER.error("Tests failed")
                await self._rollback(current_hash)
                return False

            self.last_update = datetime.now(timezone.utc)
            self.update_count += 1

            LOGGER.info("Updates applied successfully")

            # Schedule restart
            if restart_callback:
                await restart_callback()

            return True

        except Exception as e:
            LOGGER.error(f"Failed to apply updates: {e}")
            return False

    async def _rollback(self, commit_hash: str) -> bool:
        """Rollback to previous commit"""
        try:
            LOGGER.warning(f"Rolling back to {commit_hash}")
            result = await self._run_git_command(["reset", "--hard", commit_hash])
            return result == 0
        except Exception as e:
            LOGGER.error(f"Rollback failed: {e}")
            return False

    async def _get_current_hash(self) -> str:
        """Get current commit hash"""
        try:
            result = await self._run_git_command(["rev-parse", "HEAD"])
            return result.strip()
        except Exception:
            return ""

    async def _run_git_command(self, args: list) -> str:
        """Run git command"""
        cmd = ["git", "-C", self.repo_path] + args
        return await self._run_command(cmd)

    async def _run_command(self, args: list) -> int:
        """Run shell command"""
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            return process.returncode
        except Exception as e:
            LOGGER.error(f"Command execution failed: {e}")
            return 1

    async def get_status(self) -> Dict[str, Any]:
        """Get updater status"""
        return {
            "enabled": self.enabled,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_update": self.last_update.isoformat() if self.last_update else None,
            "update_count": self.update_count,
        }


class GracefulShutdown:
    """Manage graceful shutdown"""

    def __init__(self):
        self.is_shutting_down = False
        self.active_tasks = set()
        self.shutdown_timeout = int(getattr(Config, "SHUTDOWN_TIMEOUT_SECONDS", 30))

    async def initiate_shutdown(self, reason: str = "Admin request") -> None:
        """Initiate graceful shutdown"""
        LOGGER.info(f"Initiating graceful shutdown: {reason}")
        self.is_shutting_down = True

        # Give tasks time to complete
        await asyncio.sleep(1)

        # Wait for active tasks
        if self.active_tasks:
            LOGGER.info(f"Waiting for {len(self.active_tasks)} active tasks to complete...")
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self.active_tasks, return_exceptions=True),
                    timeout=self.shutdown_timeout
                )
            except asyncio.TimeoutError:
                LOGGER.warning("Timeout waiting for tasks, forcing shutdown")
                for task in self.active_tasks:
                    task.cancel()

        LOGGER.info("Graceful shutdown complete")

    def add_task(self, task: asyncio.Task) -> None:
        """Register an active task"""
        self.active_tasks.add(task)
        task.add_done_callback(self.active_tasks.discard)

    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal"""
        while not self.is_shutting_down:
            await asyncio.sleep(0.1)


# Global instances
gitops_updater = GitOpsUpdater()
graceful_shutdown = GracefulShutdown()
