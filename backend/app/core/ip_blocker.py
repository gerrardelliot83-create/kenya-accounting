"""
IP Blocking Utility

Tracks and blocks IP addresses that exhibit malicious behavior:
- Failed authentication attempts
- Rate limit violations
- Suspicious activity patterns

Security Features:
- Automatic IP blocking after threshold violations
- Configurable block duration
- Automatic unblocking after time expires
- Failed attempt tracking with decay
- Thread-safe operations
- Audit logging integration

Production Notes:
- Current implementation uses in-memory storage
- For production with multiple instances, use Redis or database
- Consider integrating with threat intelligence feeds
- Implement IP whitelist for legitimate services
- Add manual block/unblock API endpoints for admins
"""

from typing import Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import logging
import asyncio
from threading import Lock


logger = logging.getLogger(__name__)


@dataclass
class IPStatus:
    """
    Track status and history for an IP address.

    Attributes:
        ip_address: The IP address
        failed_attempts: Number of failed attempts
        first_failure: Timestamp of first failed attempt
        last_failure: Timestamp of most recent failed attempt
        blocked_until: When the block expires (None if not blocked)
        total_violations: Total number of violations (all time)
    """
    ip_address: str
    failed_attempts: int = 0
    first_failure: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    blocked_until: Optional[datetime] = None
    total_violations: int = 0


class IPBlocker:
    """
    Track and block malicious IP addresses.

    Features:
    - Tracks failed authentication attempts per IP
    - Automatically blocks IPs after threshold violations
    - Automatic unblocking after configured duration
    - Decay of failed attempts over time
    - Thread-safe operations
    """

    def __init__(
        self,
        block_threshold: int = 10,
        block_duration_minutes: int = 60,
        attempt_window_minutes: int = 15,
        cleanup_interval_seconds: int = 300
    ):
        """
        Initialize IP blocker.

        Args:
            block_threshold: Number of failures before blocking (default: 10)
            block_duration_minutes: How long to block IPs (default: 60 minutes)
            attempt_window_minutes: Time window for counting attempts (default: 15 minutes)
            cleanup_interval_seconds: How often to cleanup expired blocks (default: 300s)
        """
        self.block_threshold = block_threshold
        self.block_duration = timedelta(minutes=block_duration_minutes)
        self.attempt_window = timedelta(minutes=attempt_window_minutes)
        self.cleanup_interval = cleanup_interval_seconds

        # Track IP status
        self.ip_status: Dict[str, IPStatus] = {}

        # Thread safety
        self._lock = Lock()

        # Start cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info(
            f"IPBlocker initialized: threshold={block_threshold}, "
            f"duration={block_duration_minutes}m, window={attempt_window_minutes}m"
        )

    def start_cleanup_task(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        Start background cleanup task.

        Args:
            loop: Event loop to run cleanup task in
        """
        if self._cleanup_task is None:
            self._cleanup_task = loop.create_task(self._cleanup_loop())
            logger.info("IP blocker cleanup task started")

    async def _cleanup_loop(self) -> None:
        """
        Background task to cleanup expired blocks and old attempts.
        """
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                self._cleanup_expired()
            except asyncio.CancelledError:
                logger.info("IP blocker cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in IP blocker cleanup: {e}", exc_info=True)

    def _cleanup_expired(self) -> None:
        """
        Remove expired blocks and old attempt records.
        """
        now = datetime.utcnow()
        cleaned_count = 0

        with self._lock:
            # Find expired entries
            expired_ips = []

            for ip, status in self.ip_status.items():
                # Check if block expired
                if status.blocked_until and now >= status.blocked_until:
                    status.blocked_until = None
                    status.failed_attempts = 0
                    logger.info(f"IP {ip} unblocked after timeout")

                # Remove old attempt records (outside attempt window)
                if (
                    status.last_failure and
                    not status.blocked_until and
                    now - status.last_failure > self.attempt_window * 2
                ):
                    expired_ips.append(ip)
                    cleaned_count += 1

            # Remove expired entries
            for ip in expired_ips:
                del self.ip_status[ip]

        if cleaned_count > 0:
            logger.debug(f"Cleaned up {cleaned_count} expired IP records")

    def record_failed_attempt(self, ip: str, reason: str = "authentication_failed") -> bool:
        """
        Record a failed attempt from an IP address.

        Args:
            ip: IP address
            reason: Reason for failure (for logging)

        Returns:
            True if IP should be blocked, False otherwise
        """
        now = datetime.utcnow()

        with self._lock:
            # Get or create IP status
            if ip not in self.ip_status:
                self.ip_status[ip] = IPStatus(ip_address=ip)

            status = self.ip_status[ip]

            # Check if attempts are within the window
            if status.first_failure and now - status.first_failure > self.attempt_window:
                # Reset counter if outside window
                status.failed_attempts = 0
                status.first_failure = now

            # Record attempt
            if status.failed_attempts == 0:
                status.first_failure = now

            status.failed_attempts += 1
            status.last_failure = now
            status.total_violations += 1

            logger.warning(
                f"Failed attempt from {ip}: {reason} "
                f"(count: {status.failed_attempts}/{self.block_threshold})"
            )

            # Check if threshold reached
            if status.failed_attempts >= self.block_threshold:
                self.block_ip(ip, reason=reason)
                return True

            return False

    def block_ip(self, ip: str, reason: str = "threshold_exceeded") -> None:
        """
        Block an IP address.

        Args:
            ip: IP address to block
            reason: Reason for blocking (for logging)
        """
        now = datetime.utcnow()

        with self._lock:
            if ip not in self.ip_status:
                self.ip_status[ip] = IPStatus(ip_address=ip)

            status = self.ip_status[ip]
            status.blocked_until = now + self.block_duration

            logger.error(
                f"IP {ip} BLOCKED for {self.block_duration.total_seconds() / 60} minutes. "
                f"Reason: {reason}. "
                f"Total failures: {status.failed_attempts}, "
                f"Total violations: {status.total_violations}"
            )

    def unblock_ip(self, ip: str) -> bool:
        """
        Manually unblock an IP address.

        Args:
            ip: IP address to unblock

        Returns:
            True if IP was blocked and is now unblocked, False otherwise
        """
        with self._lock:
            if ip in self.ip_status:
                status = self.ip_status[ip]
                if status.blocked_until:
                    status.blocked_until = None
                    status.failed_attempts = 0
                    logger.info(f"IP {ip} manually unblocked")
                    return True

        return False

    def is_blocked(self, ip: str) -> bool:
        """
        Check if an IP address is blocked.

        Args:
            ip: IP address to check

        Returns:
            True if IP is blocked, False otherwise
        """
        now = datetime.utcnow()

        with self._lock:
            if ip in self.ip_status:
                status = self.ip_status[ip]
                if status.blocked_until:
                    if now < status.blocked_until:
                        # Still blocked
                        return True
                    else:
                        # Block expired, clean up
                        status.blocked_until = None
                        status.failed_attempts = 0
                        logger.info(f"IP {ip} unblocked (timeout)")

        return False

    def get_block_info(self, ip: str) -> Optional[Dict]:
        """
        Get blocking information for an IP address.

        Args:
            ip: IP address

        Returns:
            Dictionary with block info, or None if not tracked
        """
        with self._lock:
            if ip not in self.ip_status:
                return None

            status = self.ip_status[ip]
            now = datetime.utcnow()

            return {
                "ip_address": ip,
                "is_blocked": status.blocked_until is not None and now < status.blocked_until,
                "blocked_until": status.blocked_until.isoformat() if status.blocked_until else None,
                "failed_attempts": status.failed_attempts,
                "first_failure": status.first_failure.isoformat() if status.first_failure else None,
                "last_failure": status.last_failure.isoformat() if status.last_failure else None,
                "total_violations": status.total_violations,
            }

    def clear_failed_attempts(self, ip: str) -> None:
        """
        Clear failed attempts for an IP (e.g., after successful auth).

        Args:
            ip: IP address
        """
        with self._lock:
            if ip in self.ip_status:
                status = self.ip_status[ip]
                status.failed_attempts = 0
                status.first_failure = None
                logger.debug(f"Cleared failed attempts for {ip}")

    def get_statistics(self) -> Dict:
        """
        Get overall statistics about IP blocking.

        Returns:
            Dictionary with statistics
        """
        now = datetime.utcnow()

        with self._lock:
            blocked_count = 0
            tracking_count = len(self.ip_status)
            total_violations = 0

            for status in self.ip_status.values():
                if status.blocked_until and now < status.blocked_until:
                    blocked_count += 1
                total_violations += status.total_violations

            return {
                "blocked_ips": blocked_count,
                "tracked_ips": tracking_count,
                "total_violations_all_time": total_violations,
                "block_threshold": self.block_threshold,
                "block_duration_minutes": self.block_duration.total_seconds() / 60,
            }


# Check if we're in testing mode
import os
_environment = os.getenv("ENVIRONMENT", "development").lower()
_is_testing = os.getenv("TESTING", "false").lower() == "true" or _environment == "testing"

# Global IP blocker instance
# In production, consider using Redis or database for persistence
if _is_testing:
    # Testing mode: relaxed thresholds to allow test suites to run
    ip_blocker = IPBlocker(
        block_threshold=1000,  # Block after 1000 failed attempts
        block_duration_minutes=1,  # Block for 1 minute
        attempt_window_minutes=15,  # Count attempts within 15 minutes
        cleanup_interval_seconds=60  # Cleanup every 1 minute
    )
    logger.info("IP blocker running in TESTING mode with relaxed thresholds")
else:
    # Production mode: strict security thresholds
    ip_blocker = IPBlocker(
        block_threshold=10,  # Block after 10 failed attempts
        block_duration_minutes=60,  # Block for 60 minutes
        attempt_window_minutes=15,  # Count attempts within 15 minutes
        cleanup_interval_seconds=300  # Cleanup every 5 minutes
    )


def get_ip_blocker() -> IPBlocker:
    """
    Get the global IP blocker instance.

    Returns:
        IPBlocker instance
    """
    return ip_blocker
