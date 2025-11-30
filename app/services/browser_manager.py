"""Browser lifecycle management service."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from datetime import datetime

from browser_use import Browser

from app.config import get_settings

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages browser instances with lifecycle and memory tracking."""

    def __init__(self):
        """Initialize browser manager."""
        self.settings = get_settings()
        self._active_browsers: Dict[str, Dict[str, Any]] = {}
        self._browser_lock = asyncio.Lock()
        self._browser_counter = 0

    @property
    def active_count(self) -> int:
        """Get the count of active browsers."""
        return len(self._active_browsers)

    @property
    def is_available(self) -> bool:
        """Check if we can create a new browser instance."""
        return self.active_count < self.settings.max_concurrent_browsers

    async def _wait_for_availability(self, timeout: float = 30.0) -> bool:
        """Wait for a browser slot to become available."""
        start_time = asyncio.get_event_loop().time()

        while not self.is_available:
            if asyncio.get_event_loop().time() - start_time > timeout:
                return False

            await asyncio.sleep(0.5)

        return True

    @asynccontextmanager
    async def get_browser(self, task_id: Optional[str] = None):
        """
        Get a browser instance with proper lifecycle management.

        Args:
            task_id: Optional task identifier for tracking

        Yields:
            Browser instance configured for Railway/Docker environment
        """
        browser = None
        browser_id = None

        try:
            # Wait for available slot
            async with self._browser_lock:
                if not await self._wait_for_availability():
                    raise RuntimeError(
                        f"No browser slots available (max: {self.settings.max_concurrent_browsers})"
                    )

                # Generate unique browser ID
                self._browser_counter += 1
                browser_id = f"browser_{self._browser_counter}"

                # Log browser mode
                browser_mode = "headless" if self.settings.headless_browser else "headed (GUI)"
                logger.info(
                    f"Creating browser {browser_id} for task {task_id} in {browser_mode} mode "
                    f"({self.active_count + 1}/{self.settings.max_concurrent_browsers} active)"
                )

            # Create browser with configurable headless mode
            browser = Browser(
                headless=self.settings.headless_browser,  # Use config setting
                disable_security=False,  # Keep security enabled
                args=self.settings.chromium_args,  # Use 'args' instead of 'extra_chromium_args'
            )

            # Track browser instance
            async with self._browser_lock:
                self._active_browsers[browser_id] = {
                    "browser": browser,
                    "task_id": task_id,
                    "created_at": datetime.utcnow(),
                }

            yield browser

        except Exception as e:
            logger.error(f"Error in browser {browser_id}: {e}")
            raise

        finally:
            # Clean up browser
            if browser:
                try:
                    await browser.close()
                    logger.info(f"Closed browser {browser_id}")
                except Exception as e:
                    logger.error(f"Error closing browser {browser_id}: {e}")

            # Remove from tracking
            if browser_id:
                async with self._browser_lock:
                    self._active_browsers.pop(browser_id, None)
                    logger.info(
                        f"Removed browser {browser_id} from tracking "
                        f"({self.active_count}/{self.settings.max_concurrent_browsers} active)"
                    )

    async def cleanup_all(self):
        """Clean up all active browser instances."""
        logger.info(f"Cleaning up {self.active_count} active browsers")

        async with self._browser_lock:
            browsers_to_close = list(self._active_browsers.values())
            self._active_browsers.clear()

        # Close all browsers
        close_tasks = []
        for browser_info in browsers_to_close:
            browser = browser_info.get("browser")
            if browser:
                close_tasks.append(browser.close())

        if close_tasks:
            results = await asyncio.gather(*close_tasks, return_exceptions=True)
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error closing browser {i}: {result}")

        logger.info("All browsers cleaned up")

    def get_status(self) -> Dict[str, Any]:
        """Get current browser manager status."""
        return {
            "active_browsers": self.active_count,
            "max_browsers": self.settings.max_concurrent_browsers,
            "available_slots": self.settings.max_concurrent_browsers - self.active_count,
            "is_available": self.is_available,
            "browser_mode": "headless" if self.settings.headless_browser else "headed (GUI)",
            "browser_details": [
                {
                    "task_id": info["task_id"],
                    "created_at": info["created_at"].isoformat(),
                    "age_seconds": (datetime.utcnow() - info["created_at"]).total_seconds(),
                }
                for info in self._active_browsers.values()
            ],
        }


# Global browser manager instance
_browser_manager: Optional[BrowserManager] = None


def get_browser_manager() -> BrowserManager:
    """Get or create the global browser manager instance."""
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserManager()
    return _browser_manager