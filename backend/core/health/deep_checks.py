"""
Deep health checks for production monitoring.

Goes beyond "is server running" to check actual health.
"""
from dataclasses import dataclass
from typing import List, Dict
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health check status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class HealthResult:
    """Result of health check."""
    status: HealthStatus
    message: str = ""
    response_time_ms: float = 0
    details: Dict = None


class HealthChecker:
    """Comprehensive health checks."""

    def __init__(self, db, redis, sms_provider, ai_service):
        self.db = db
        self.redis = redis
        self.sms = sms_provider
        self.ai = ai_service

    async def check_all(self) -> Dict[str, HealthResult]:
        """Run all health checks."""
        results = {
            "database": await self.check_database(),
            "redis": await self.check_redis(),
            "sms_provider": await self.check_sms_provider(),
            "ai_service": await self.check_ai_service()
        }

        # Overall status: worst of individual checks
        overall_status = self._aggregate_status(results)

        results["overall"] = HealthResult(
            status=overall_status,
            message=f"System is {overall_status.value}"
        )

        return results

    async def check_database(self) -> HealthResult:
        """Check database health."""
        try:
            start = time.time()

            # Check connection pool
            pool_status = await self.db.get_pool_status()

            if pool_status["available"] < 2:
                return HealthResult(
                    status=HealthStatus.DEGRADED,
                    message="connection_pool_low",
                    details={"available": pool_status["available"]}
                )

            # Check query performance
            await self.db.execute("SELECT 1")
            response_time = (time.time() - start) * 1000

            if response_time > 1000:
                return HealthResult(
                    status=HealthStatus.DEGRADED,
                    message="slow_queries",
                    response_time_ms=response_time
                )

            # Check disk space
            disk_usage = await self.db.get_disk_usage()
            if disk_usage > 90:
                return HealthResult(
                    status=HealthStatus.DEGRADED,
                    message="low_disk_space",
                    details={"disk_usage_percent": disk_usage}
                )

            return HealthResult(
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time
            )

        except Exception as e:
            logger.error("db_health_check_failed", error=str(e))
            return HealthResult(
                status=HealthStatus.UNHEALTHY,
                message=str(e)
            )

    async def check_redis(self) -> HealthResult:
        """Check Redis health."""
        try:
            start = time.time()

            # Ping Redis
            pong = await self.redis.ping()

            if not pong:
                return HealthResult(
                    status=HealthStatus.UNHEALTHY,
                    message="redis_ping_failed"
                )

            response_time = (time.time() - start) * 1000

            # Check memory usage
            info = await self.redis.info("memory")
            used_memory_percent = (
                int(info["used_memory"]) /
                int(info["maxmemory"]) * 100
                if info.get("maxmemory") else 0
            )

            if used_memory_percent > 90:
                return HealthResult(
                    status=HealthStatus.DEGRADED,
                    message="redis_memory_high",
                    details={"memory_usage_percent": used_memory_percent}
                )

            return HealthResult(
                status=HealthStatus.HEALTHY,
                response_time_ms=response_time
            )

        except Exception as e:
            logger.error("redis_health_check_failed", error=str(e))
            return HealthResult(
                status=HealthStatus.UNHEALTHY,
                message=str(e)
            )

    async def check_sms_provider(self) -> HealthResult:
        """Check SMS provider health."""
        try:
            # Check Twilio account status (don't send actual SMS)
            account = await self.sms.get_account_status()

            if account["status"] != "active":
                return HealthResult(
                    status=HealthStatus.UNHEALTHY,
                    message=f"sms_account_{account['status']}"
                )

            # Check balance
            balance = float(account.get("balance", "0"))
            if balance < 10:  # Less than $10
                return HealthResult(
                    status=HealthStatus.DEGRADED,
                    message="low_sms_balance",
                    details={"balance": balance}
                )

            return HealthResult(
                status=HealthStatus.HEALTHY,
                details={"balance": balance}
            )

        except Exception as e:
            logger.error("sms_health_check_failed", error=str(e))
            return HealthResult(
                status=HealthStatus.UNHEALTHY,
                message=str(e)
            )

    async def check_ai_service(self) -> HealthResult:
        """Check AI service health."""
        try:
            # Check request queue
            metrics = await self.ai.get_metrics()

            queue_size = metrics.get("queue_size", 0)

            if queue_size > 50:
                return HealthResult(
                    status=HealthStatus.DEGRADED,
                    message="ai_queue_backed_up",
                    details={"queue_size": queue_size}
                )

            # Check error rate
            total = metrics.get("total_requests", 0)
            failed = metrics.get("failed", 0)

            if total > 0:
                error_rate = (failed / total) * 100

                if error_rate > 25:
                    return HealthResult(
                        status=HealthStatus.DEGRADED,
                        message="high_ai_error_rate",
                        details={"error_rate_percent": error_rate}
                    )

            return HealthResult(
                status=HealthStatus.HEALTHY,
                details=metrics
            )

        except Exception as e:
            logger.error("ai_health_check_failed", error=str(e))
            return HealthResult(
                status=HealthStatus.UNHEALTHY,
                message=str(e)
            )

    def _aggregate_status(self, results: Dict[str, HealthResult]) -> HealthStatus:
        """Aggregate individual statuses to overall status."""
        statuses = [r.status for r in results.values()]

        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
