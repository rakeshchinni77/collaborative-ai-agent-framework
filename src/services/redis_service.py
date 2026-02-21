from src.services.logger import get_logger
import json
from typing import Any, Optional, Final
import redis
from redis.exceptions import RedisError
from src.config import settings


# Redis Key Builder Utility
class RedisKeyBuilder:
    """
    Centralized Redis key builder to ensure consistent key formats
    across the entire application.
    """

    TASK_WORKSPACE_SUFFIX: Final[str] = "workspace"
    TASK_PREFIX: Final[str] = "task"

    @classmethod
    def task_workspace_key(cls, task_id: str) -> str:
        """
        Generates the Redis key for a task workspace.

        Required format:
        task:<task_id>:workspace
        """
        if not task_id or not isinstance(task_id, str):
            raise ValueError("task_id must be a non-empty string")

        return f"{cls.TASK_PREFIX}:{task_id}:{cls.TASK_WORKSPACE_SUFFIX}"


class RedisService:
    """
    Centralized Redis client with connection pooling.
    Provides helper methods for:
    - health checks
    - get/set/delete operations
    - JSON serialization
    """

    def __init__(self) -> None:
        self._client = None
        self._logger = get_logger("redis_service")
        self._initialize_client()

    def _initialize_client(self) -> None:
        """
        Initializes Redis connection pool and client.
        Health-safe: does not raise exception if Redis is unavailable.
        """
        try:
            pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=10,
                socket_timeout=5,
                socket_connect_timeout=5,
            )
            self._client = redis.Redis(connection_pool=pool)

            # Optional ping to validate connection during startup
            self._client.ping()

        except RedisError:
            self._client = None

    # Health Check
    def ping(self) -> bool:
        """
        Checks Redis connectivity.

        Used by:
        - Health endpoint
        - Debug verification
        - Infra readiness checks
        """
        if not self._client:
            self._logger.error(
                "Redis client not initialized",
                extra={"service": "redis_service", "operation": "ping"},
            )
            return False

        try:
            result = self._client.ping()

            if result:
                self._logger.info(
                    "Redis ping successful",
                    extra={"service": "redis_service", "operation": "ping"},
                )

            return result

        except RedisError as e:
            self._logger.error(
                "Redis ping failed",
                extra={
                    "service": "redis_service",
                    "operation": "ping",
                    "error": str(e),
                },
            )
            return False

    # Basic Key Operations
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        Stores value in Redis.
        Automatically serializes dict/list to JSON.
        """
        if not self._client:
            return False

        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)

            return self._client.set(name=key, value=value, ex=expire)
        except RedisError:
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves value from Redis.
        Automatically deserializes JSON if applicable.
        """
        if not self._client:
            return None

        try:
            value = self._client.get(name=key)

            if value is None:
                return None

            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value

        except RedisError:
            return None

    def delete(self, key: str) -> bool:
        if not self._client:
            return False

        try:
            return self._client.delete(key) > 0
        except RedisError:
            return False
          
    def set_workspace(self, task_id: str, data: dict) -> bool:
        if not self._client:
            self._logger.error(
                "Redis client not initialized",
                extra={"service": "redis_service", "operation": "set_workspace"},
            )
            return False

        if not isinstance(task_id, str) or not task_id:
            raise ValueError("task_id must be a non-empty string")

        if not isinstance(data, dict):
            raise ValueError("workspace data must be a dictionary")

        try:
            key = RedisKeyBuilder.task_workspace_key(task_id)
            payload = json.dumps(data)
        except (TypeError, ValueError) as e:
            self._logger.error(
                "JSON serialization failed",
                extra={
                    "service": "redis_service",
                    "operation": "set_workspace",
                    "task_id": task_id,
                    "error": str(e),
                },
            )
            return False

        try:
            return self._client.set(name=key, value=payload)
        except RedisError as e:
            self._logger.error(
                "Redis SET operation failed",
                extra={
                    "service": "redis_service",
                    "operation": "set_workspace",
                    "task_id": task_id,
                    "error": str(e),
                },
            )
            return False
          
    def get_workspace(self, task_id: str) -> Optional[dict]:
        if not self._client:
            self._logger.error(
                "Redis client not initialized",
                extra={"service": "redis_service", "operation": "get_workspace"},
            )
            return None

        if not isinstance(task_id, str) or not task_id:
            raise ValueError("task_id must be a non-empty string")

        try:
            key = RedisKeyBuilder.task_workspace_key(task_id)
            value = self._client.get(name=key)
        except RedisError as e:
            self._logger.error(
                "Redis GET operation failed",
                extra={
                    "service": "redis_service",
                    "operation": "get_workspace",
                    "task_id": task_id,
                    "error": str(e),
                },
            )
            return None

        if value is None:
            return None

        try:
            data = json.loads(value)
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError as e:
            self._logger.error(
                "JSON deserialization failed",
                extra={
                    "service": "redis_service",
                    "operation": "get_workspace",
                    "task_id": task_id,
                    "error": str(e),
                },
            )
            return None

    def delete_workspace(self, task_id: str) -> bool:
        if not self._client:
            self._logger.error(
                "Redis client not initialized",
                extra={"service": "redis_service", "operation": "delete_workspace"},
            )
            return False

        if not isinstance(task_id, str) or not task_id:
            raise ValueError("task_id must be a non-empty string")

        try:
            key = RedisKeyBuilder.task_workspace_key(task_id)
            return self._client.delete(key) > 0
        except RedisError as e:
            self._logger.error(
                "Redis DELETE operation failed",
                extra={
                    "service": "redis_service",
                    "operation": "delete_workspace",
                    "task_id": task_id,
                    "error": str(e),
                },
            )
            return False

# Singleton Redis service instance
redis_service = RedisService()
