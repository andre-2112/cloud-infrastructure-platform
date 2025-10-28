"""
State Manager

Tracks deployment state, operation history, and stack status.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import yaml
import json

from ..utils.logger import get_logger

logger = get_logger(__name__)


class DeploymentStatus(Enum):
    """Deployment status"""

    INITIALIZED = "initialized"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"
    PARTIAL = "partial"  # Some stacks deployed, some failed
    UNKNOWN = "unknown"


class StackStatus(Enum):
    """Individual stack status"""

    NOT_DEPLOYED = "not_deployed"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    FAILED = "failed"
    DESTROYING = "destroying"
    DESTROYED = "destroyed"


class StateManager:
    """Manages deployment and stack state"""

    def __init__(self, deployment_dir: Path):
        """
        Initialize state manager

        Args:
            deployment_dir: Path to deployment directory
        """
        self.deployment_dir = Path(deployment_dir)
        self.state_file = self.deployment_dir / ".deployment-state.yaml"
        self.history_file = self.deployment_dir / ".operation-history.jsonl"

        # Initialize state file if it doesn't exist
        if not self.state_file.exists():
            self._initialize_state()

    def _initialize_state(self) -> None:
        """Initialize state file"""
        initial_state = {
            "deployment_status": DeploymentStatus.INITIALIZED.value,
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "stacks": {},
            "current_operation": None,
        }

        with open(self.state_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(initial_state, f)

        logger.debug(f"Initialized state file: {self.state_file}")

    def load_state(self) -> Dict[str, Any]:
        """
        Load current state

        Returns:
            State dictionary
        """
        if not self.state_file.exists():
            self._initialize_state()

        with open(self.state_file, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def save_state(self, state: Dict[str, Any]) -> None:
        """
        Save state

        Args:
            state: State dictionary
        """
        state["last_updated"] = datetime.utcnow().isoformat() + "Z"

        with open(self.state_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(state, f, default_flow_style=False)

    def set_deployment_status(self, status: DeploymentStatus) -> None:
        """
        Set deployment status

        Args:
            status: New status
        """
        state = self.load_state()
        state["deployment_status"] = status.value
        self.save_state(state)

        logger.info(f"Deployment status set to: {status.value}")

    def get_deployment_status(self) -> DeploymentStatus:
        """
        Get current deployment status

        Returns:
            DeploymentStatus
        """
        state = self.load_state()
        status_str = state.get("deployment_status", "unknown")

        try:
            return DeploymentStatus(status_str)
        except ValueError:
            return DeploymentStatus.UNKNOWN

    def set_stack_status(
        self, stack_name: str, status: StackStatus, environment: str = "dev"
    ) -> None:
        """
        Set stack status

        Args:
            stack_name: Name of the stack
            status: New status
            environment: Environment name
        """
        state = self.load_state()

        if "stacks" not in state:
            state["stacks"] = {}

        stack_key = f"{stack_name}-{environment}"

        state["stacks"][stack_key] = {
            "stack_name": stack_name,
            "environment": environment,
            "status": status.value,
            "last_updated": datetime.utcnow().isoformat() + "Z",
        }

        self.save_state(state)

    def get_stack_status(
        self, stack_name: str, environment: str = "dev"
    ) -> StackStatus:
        """
        Get stack status

        Args:
            stack_name: Name of the stack
            environment: Environment name

        Returns:
            StackStatus
        """
        state = self.load_state()
        stack_key = f"{stack_name}-{environment}"

        stack_state = state.get("stacks", {}).get(stack_key)

        if not stack_state:
            return StackStatus.NOT_DEPLOYED

        status_str = stack_state.get("status", "not_deployed")

        try:
            return StackStatus(status_str)
        except ValueError:
            return StackStatus.NOT_DEPLOYED

    def get_all_stack_statuses(self, environment: str = "dev") -> Dict[str, StackStatus]:
        """
        Get all stack statuses for an environment

        Args:
            environment: Environment name

        Returns:
            Dictionary of stack_name -> StackStatus
        """
        state = self.load_state()
        result = {}

        for stack_key, stack_state in state.get("stacks", {}).items():
            if stack_state.get("environment") == environment:
                stack_name = stack_state.get("stack_name")
                status_str = stack_state.get("status", "not_deployed")

                try:
                    result[stack_name] = StackStatus(status_str)
                except ValueError:
                    result[stack_name] = StackStatus.NOT_DEPLOYED

        return result

    def record_operation(
        self,
        operation_type: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record an operation in history

        Args:
            operation_type: Type of operation (deploy, destroy, etc.)
            status: Status (started, completed, failed)
            details: Optional operation details
        """
        operation_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "operation": operation_type,
            "status": status,
            "details": details or {},
        }

        # Append to history file (JSONL format)
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(operation_record) + "\n")

        logger.debug(f"Recorded operation: {operation_type} - {status}")

    def get_operation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get operation history

        Args:
            limit: Maximum number of records to return

        Returns:
            List of operation records (most recent first)
        """
        if not self.history_file.exists():
            return []

        records = []

        with open(self.history_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    records.append(record)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid history record: {line}")

        # Return most recent records
        return list(reversed(records))[:limit]

    def start_operation(
        self, operation_type: str, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Mark operation as started

        Args:
            operation_type: Type of operation
            details: Operation details
        """
        state = self.load_state()
        state["current_operation"] = {
            "type": operation_type,
            "started_at": datetime.utcnow().isoformat() + "Z",
            "details": details or {},
        }
        self.save_state(state)

        self.record_operation(operation_type, "started", details)

    def complete_operation(
        self, success: bool, details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Mark current operation as complete

        Args:
            success: Whether operation succeeded
            details: Completion details
        """
        state = self.load_state()
        current_op = state.get("current_operation")

        if current_op:
            operation_type = current_op.get("type", "unknown")
            status = "completed" if success else "failed"

            self.record_operation(operation_type, status, details)

            state["current_operation"] = None
            self.save_state(state)

    def get_current_operation(self) -> Optional[Dict[str, Any]]:
        """
        Get current operation if any

        Returns:
            Current operation info, or None
        """
        state = self.load_state()
        return state.get("current_operation")

    def is_operation_in_progress(self) -> bool:
        """
        Check if an operation is currently in progress

        Returns:
            True if operation in progress
        """
        return self.get_current_operation() is not None

    def get_deployment_summary(self, environment: str = "dev") -> Dict[str, Any]:
        """
        Get deployment summary

        Args:
            environment: Environment name

        Returns:
            Summary dictionary
        """
        state = self.load_state()
        stack_statuses = self.get_all_stack_statuses(environment)

        deployed_count = sum(
            1 for status in stack_statuses.values() if status == StackStatus.DEPLOYED
        )
        failed_count = sum(
            1 for status in stack_statuses.values() if status == StackStatus.FAILED
        )

        return {
            "deployment_status": state.get("deployment_status"),
            "last_updated": state.get("last_updated"),
            "environment": environment,
            "total_stacks": len(stack_statuses),
            "deployed_stacks": deployed_count,
            "failed_stacks": failed_count,
            "current_operation": self.get_current_operation(),
            "stack_statuses": {
                name: status.value for name, status in stack_statuses.items()
            },
        }
