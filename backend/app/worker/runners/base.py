import asyncio
import os
import re
import shutil
from typing import List, Optional, Tuple
from app.core.errors import AppError
from app.core.logging import logger

# Strict hostname and flag sanitization regex
TARGET_REGEX = re.compile(r"^[a-zA-Z0-9](?:[a-zA-Z0-9-_]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9-_]{1,63})+$")


class SubprocessExecutionError(AppError):
    """Raised when a subprocess fails or exits with an unexpected error code."""
    def __init__(self, command: str, exit_code: int, stderr: str):
        message = f"Command '{command}' failed with exit code {exit_code}: {stderr}"
        super().__init__(message, code="SUBPROCESS_ERROR")
        self.exit_code = exit_code
        self.stderr = stderr


def validate_target_arg(target: str) -> str:
    """
    Validates that a CLI target argument is a clean hostname without
    injection flags or leading hyphens.
    """
    clean = target.strip()
    if clean.startswith("-"):
        raise ValueError(f"Target '{target}' cannot start with a hyphen (flag injection attempt).")
    if not TARGET_REGEX.match(clean):
        raise ValueError(f"Target '{target}' does not match valid hostname pattern.")
    return clean


async def safe_subprocess_exec(
    cmd: List[str],
    timeout_seconds: int = 60,
    check_exit_code: bool = True,
) -> Tuple[int, str, str]:
    """
    Safely executes an external CLI binary:
    - Never uses shell=True.
    - Pre-verifies binary exists in PATH.
    - Enforces hard process timeout with process tree termination.
    - Captures stdout and stderr cleanly.
    """
    if not cmd or not isinstance(cmd, list):
        raise ValueError("Command must be a non-empty list of string arguments.")

    binary_name = cmd[0]
    binary_path = shutil.which(binary_name)
    if not binary_path:
        logger.warning(f"Binary '{binary_name}' was not found in system PATH.")
        return (-1, "", f"Binary '{binary_name}' not installed on system.")

    logger.debug(f"Executing: {' '.join(cmd)} (timeout: {timeout_seconds}s)")

    proc = await asyncio.create_subprocess_exec(
        binary_path,
        *cmd[1:],
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(),
            timeout=timeout_seconds,
        )
        stdout_str = stdout_bytes.decode("utf-8", errors="replace")
        stderr_str = stderr_bytes.decode("utf-8", errors="replace")
        exit_code = proc.returncode or 0

        if check_exit_code and exit_code != 0:
            logger.warning(f"Subprocess '{binary_name}' exited with {exit_code}: {stderr_str}")

        return (exit_code, stdout_str, stderr_str)

    except asyncio.TimeoutError:
        logger.error(f"Process '{' '.join(cmd)}' exceeded timeout of {timeout_seconds}s. Terminating...")
        try:
            proc.terminate()
            await asyncio.sleep(0.5)
            if proc.returncode is None:
                proc.kill()
        except ProcessLookupError:
            pass
        return (-1, "", f"Command timed out after {timeout_seconds} seconds.")
