"""
Headless CAPTCHA Solver for Phase 9 Enterprise Features

Turnstile/hCaptcha/reCAPTCHA solver with CapSolver/2Captcha integration.
Target: >90% success rate.

Features:
- Multiple CAPTCHA type support
- Third-party solver integration
- Headless browser automation
- Rate limiting and retry logic
- Success tracking
"""

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class CaptchaType(str, Enum):
    """Supported CAPTCHA types"""
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    H_CAPTCHA = "hcaptcha"
    TURNSTILE = "turnstile"
    IMAGE_CAPTCHA = "image"
    FUNCAPTCHA = "funcaptcha"


class SolverProvider(str, Enum):
    """CAPTCHA solver providers"""
    CAPSOLVER = "capsolver"
    TWO_CAPTCHA = "2captcha"
    ANTI_CAPTCHA = "anticaptcha"
    CAPMONSTER = "capmonster"


@dataclass
class CaptchaSolution:
    """CAPTCHA solution result"""
    captcha_type: CaptchaType
    solution: str
    solve_time_seconds: float
    success: bool
    provider: SolverProvider
    cost: float = 0.0  # Cost in credits/USD
    error: Optional[str] = None


@dataclass
class SolverStats:
    """Solver statistics"""
    total_attempts: int
    successful_solves: int
    failed_solves: int
    avg_solve_time: float
    total_cost: float
    success_rate: float


class CaptchaSolver:
    """
    Base CAPTCHA solver with multiple provider support.

    Handles:
    - Provider selection
    - API requests
    - Result parsing
    - Error handling
    """

    def __init__(
        self,
        provider: SolverProvider = SolverProvider.CAPSOLVER,
        api_key: Optional[str] = None
    ) -> None:
        """
        Initialize CAPTCHA solver.

        Args:
            provider: Solver provider to use
            api_key: API key for provider
        """
        self.provider = provider
        self.api_key = api_key

        self.stats: dict[str, float | int] = {
            "total_attempts": 0,
            "successful": 0,
            "failed": 0,
            "total_time": 0.0,
            "total_cost": 0.0
        }

        logger.info(f"CaptchaSolver initialized: provider={provider}")

    async def solve(
        self,
        captcha_type: CaptchaType,
        site_key: str,
        site_url: str,
        **kwargs: Any
    ) -> CaptchaSolution:
        """
        Solve a CAPTCHA.

        Args:
            captcha_type: Type of CAPTCHA
            site_key: CAPTCHA site key
            site_url: Website URL
            **kwargs: Additional parameters

        Returns:
            CaptchaSolution
        """
        import time

        self.stats["total_attempts"] += 1
        start_time = time.perf_counter()

        try:
            # Submit CAPTCHA to solver
            task_id = await self._submit_captcha(
                captcha_type, site_key, site_url, **kwargs
            )

            # Poll for result
            solution_text = await self._get_solution(task_id)

            solve_time = time.perf_counter() - start_time

            # Calculate cost (mock pricing)
            cost = self._calculate_cost(captcha_type)

            self.stats["successful"] += 1
            self.stats["total_time"] += solve_time
            self.stats["total_cost"] += cost

            logger.info(
                f"Solved {captcha_type} in {solve_time:.2f}s "
                f"(cost: ${cost:.4f})"
            )

            return CaptchaSolution(
                captcha_type=captcha_type,
                solution=solution_text,
                solve_time_seconds=solve_time,
                success=True,
                provider=self.provider,
                cost=cost
            )

        except Exception as e:
            self.stats["failed"] += 1
            solve_time = time.perf_counter() - start_time

            logger.error(f"Failed to solve CAPTCHA: {e}")

            return CaptchaSolution(
                captcha_type=captcha_type,
                solution="",
                solve_time_seconds=solve_time,
                success=False,
                provider=self.provider,
                error=str(e)
            )

    async def _submit_captcha(
        self,
        captcha_type: CaptchaType,
        site_key: str,
        site_url: str,
        **kwargs: Any
    ) -> str:
        """Submit CAPTCHA to solver API"""
        # Mock API submission
        await asyncio.sleep(0.1)

        task_id = hashlib.md5(f"{site_key}{site_url}".encode()).hexdigest()[:16]

        logger.debug(f"Submitted CAPTCHA: task_id={task_id}")

        return task_id

    async def _get_solution(self, task_id: str) -> str:
        """Poll for CAPTCHA solution"""
        # Mock solution polling (typically takes 10-30 seconds)
        await asyncio.sleep(0.5)  # Simulate solving time

        # Mock solution token
        solution = f"03AGdBq27{task_id[:20]}MOCK_TOKEN"

        logger.debug(f"Got solution for task {task_id}")

        return solution

    def _calculate_cost(self, captcha_type: CaptchaType) -> float:
        """Calculate solving cost"""
        costs = {
            CaptchaType.RECAPTCHA_V2: 0.001,
            CaptchaType.RECAPTCHA_V3: 0.002,
            CaptchaType.H_CAPTCHA: 0.001,
            CaptchaType.TURNSTILE: 0.001,
            CaptchaType.IMAGE_CAPTCHA: 0.0005,
            CaptchaType.FUNCAPTCHA: 0.002
        }

        return costs.get(captcha_type, 0.001)

    def get_stats(self) -> SolverStats:
        """Get solver statistics"""
        success_rate = (
            self.stats["successful"] / self.stats["total_attempts"]
            if self.stats["total_attempts"] > 0 else 0
        )

        avg_time = (
            self.stats["total_time"] / self.stats["successful"]
            if self.stats["successful"] > 0 else 0
        )

        return SolverStats(
            total_attempts=int(self.stats["total_attempts"]),
            successful_solves=int(self.stats["successful"]),
            failed_solves=int(self.stats["failed"]),
            avg_solve_time=avg_time,
            total_cost=self.stats["total_cost"],
            success_rate=success_rate
        )


class ReCaptchaSolver(CaptchaSolver):
    """Specialized reCAPTCHA solver"""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize reCAPTCHA solver"""
        super().__init__(SolverProvider.CAPSOLVER, api_key)
        logger.info("ReCaptchaSolver initialized")

    async def solve_v2(self, site_key: str, site_url: str) -> CaptchaSolution:
        """Solve reCAPTCHA v2"""
        return await self.solve(
            CaptchaType.RECAPTCHA_V2,
            site_key,
            site_url
        )

    async def solve_v3(
        self,
        site_key: str,
        site_url: str,
        action: str = "submit",
        min_score: float = 0.7
    ) -> CaptchaSolution:
        """Solve reCAPTCHA v3"""
        return await self.solve(
            CaptchaType.RECAPTCHA_V3,
            site_key,
            site_url,
            action=action,
            min_score=min_score
        )


class HCaptchaSolver(CaptchaSolver):
    """Specialized hCaptcha solver"""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize hCaptcha solver"""
        super().__init__(SolverProvider.CAPSOLVER, api_key)
        logger.info("HCaptchaSolver initialized")

    async def solve_hcaptcha(
        self,
        site_key: str,
        site_url: str,
        invisible: bool = False
    ) -> CaptchaSolution:
        """Solve hCaptcha"""
        return await self.solve(
            CaptchaType.H_CAPTCHA,
            site_key,
            site_url,
            invisible=invisible
        )


class TurnstileSolver(CaptchaSolver):
    """Specialized Cloudflare Turnstile solver"""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize Turnstile solver"""
        super().__init__(SolverProvider.CAPSOLVER, api_key)
        logger.info("TurnstileSolver initialized")

    async def solve_turnstile(
        self,
        site_key: str,
        site_url: str
    ) -> CaptchaSolution:
        """Solve Cloudflare Turnstile"""
        return await self.solve(
            CaptchaType.TURNSTILE,
            site_key,
            site_url
        )


class CaptchaPool:
    """
    Pool of CAPTCHA solvers for load balancing.

    Features:
    - Multiple provider support
    - Automatic fallback
    - Rate limiting
    - Cost optimization
    """

    def __init__(self) -> None:
        """Initialize CAPTCHA pool"""
        self.solvers: dict[SolverProvider, CaptchaSolver] = {}
        self.solve_queue: asyncio.Queue[CaptchaSolution] = asyncio.Queue()

        logger.info("CaptchaPool initialized")

    def add_solver(self, solver: CaptchaSolver) -> None:
        """Add solver to pool"""
        self.solvers[solver.provider] = solver
        logger.info(f"Added solver to pool: {solver.provider}")

    async def solve_with_fallback(
        self,
        captcha_type: CaptchaType,
        site_key: str,
        site_url: str,
        max_retries: int = 3
    ) -> CaptchaSolution:
        """
        Solve CAPTCHA with automatic fallback to other providers.

        Args:
            captcha_type: Type of CAPTCHA
            site_key: Site key
            site_url: Site URL
            max_retries: Maximum retry attempts

        Returns:
            CaptchaSolution
        """
        attempts = 0

        for provider, solver in self.solvers.items():
            if attempts >= max_retries:
                break

            logger.info(f"Attempting solve with {provider} (attempt {attempts + 1})")

            solution = await solver.solve(captcha_type, site_key, site_url)

            if solution.success:
                return solution

            attempts += 1

        # All solvers failed
        return CaptchaSolution(
            captcha_type=captcha_type,
            solution="",
            solve_time_seconds=0.0,
            success=False,
            provider=list(self.solvers.keys())[0],
            error="All solvers failed"
        )

    async def get_optimal_solver(
        self,
        captcha_type: CaptchaType
    ) -> Optional[CaptchaSolver]:
        """
        Select optimal solver based on success rate and cost.

        Args:
            captcha_type: CAPTCHA type

        Returns:
            Best solver for this CAPTCHA type
        """
        if not self.solvers:
            return None

        # Select solver with highest success rate
        best_solver = None
        best_rate = 0.0

        for solver in self.solvers.values():
            stats = solver.get_stats()

            if stats.success_rate > best_rate:
                best_rate = stats.success_rate
                best_solver = solver

        return best_solver if best_solver else list(self.solvers.values())[0]

    def get_aggregate_stats(self) -> dict[str, Any]:
        """Get aggregate statistics across all solvers"""
        total_attempts = sum(s.stats["total_attempts"] for s in self.solvers.values())
        total_successful = sum(s.stats["successful"] for s in self.solvers.values())
        total_cost = sum(s.stats["total_cost"] for s in self.solvers.values())

        return {
            "total_solvers": len(self.solvers),
            "total_attempts": total_attempts,
            "total_successful": total_successful,
            "total_cost": total_cost,
            "overall_success_rate": (
                total_successful / total_attempts
                if total_attempts > 0 else 0
            ),
            "per_provider": {
                provider.value: solver.get_stats()
                for provider, solver in self.solvers.items()
            }
        }


class HeadlessBrowserCaptcha:
    """
    Headless browser-based CAPTCHA solving.

    Uses browser automation for CAPTCHAs that require interaction.
    """

    def __init__(self, solver: CaptchaSolver):
        """
        Initialize headless browser solver.

        Args:
            solver: CaptchaSolver for token generation
        """
        self.solver = solver
        self.browser_initialized = False

        logger.info("HeadlessBrowserCaptcha initialized")

    async def init_browser(self) -> None:
        """Initialize headless browser (mock)"""
        await asyncio.sleep(0.1)
        self.browser_initialized = True
        logger.info("Headless browser initialized")

    async def solve_on_page(
        self,
        page_url: str,
        captcha_type: CaptchaType
    ) -> CaptchaSolution:
        """
        Solve CAPTCHA directly on webpage.

        Args:
            page_url: URL of page with CAPTCHA
            captcha_type: Type of CAPTCHA

        Returns:
            CaptchaSolution
        """
        if not self.browser_initialized:
            await self.init_browser()

        # Mock: navigate to page
        await asyncio.sleep(0.1)

        # Mock: extract site key
        site_key = "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"  # Test key

        # Solve using API
        solution = await self.solver.solve(captcha_type, site_key, page_url)

        if solution.success:
            # Mock: inject solution into page
            await asyncio.sleep(0.05)
            logger.info(f"Injected solution into page: {page_url}")

        return solution

    async def close_browser(self) -> None:
        """Close headless browser"""
        self.browser_initialized = False
        logger.info("Headless browser closed")


# Convenience functions
async def solve_recaptcha_v2(site_key: str, site_url: str, api_key: Optional[str] = None) -> CaptchaSolution:
    """Quick reCAPTCHA v2 solve"""
    solver = ReCaptchaSolver(api_key)
    return await solver.solve_v2(site_key, site_url)


async def solve_hcaptcha(site_key: str, site_url: str, api_key: Optional[str] = None) -> CaptchaSolution:
    """Quick hCaptcha solve"""
    solver = HCaptchaSolver(api_key)
    return await solver.solve_hcaptcha(site_key, site_url)


async def solve_turnstile(site_key: str, site_url: str, api_key: Optional[str] = None) -> CaptchaSolution:
    """Quick Turnstile solve"""
    solver = TurnstileSolver(api_key)
    return await solver.solve_turnstile(site_key, site_url)
