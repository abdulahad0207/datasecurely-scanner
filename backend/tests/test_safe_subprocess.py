import pytest
from app.worker.runners.base import (
    safe_subprocess_exec,
    validate_target_arg,
)


def test_validate_target_arg_valid():
    assert validate_target_arg("example.com") == "example.com"
    assert validate_target_arg("sub.domain.co.in") == "sub.domain.co.in"


def test_validate_target_arg_injection_flags():
    # Attempted CLI flag injection
    with pytest.raises(ValueError, match="cannot start with a hyphen"):
        validate_target_arg("-v")

    with pytest.raises(ValueError, match="cannot start with a hyphen"):
        validate_target_arg("--script=vuln")

    with pytest.raises(ValueError, match="cannot start with a hyphen"):
        validate_target_arg("-sV")


def test_validate_target_arg_invalid_syntax():
    with pytest.raises(ValueError, match="does not match valid hostname"):
        validate_target_arg("example; rm -rf /")

    with pytest.raises(ValueError, match="does not match valid hostname"):
        validate_target_arg("example$(whoami).com")


@pytest.mark.asyncio
async def test_safe_subprocess_exec_nonexistent_binary():
    cmd = ["nonexistent_binary_xyz_123", "--version"]
    code, stdout, stderr = await safe_subprocess_exec(cmd)
    assert code == -1
    assert "not installed" in stderr.lower()


@pytest.mark.asyncio
async def test_safe_subprocess_exec_timeout():
    # Run a command that sleeps longer than timeout
    import sys
    cmd = [sys.executable, "-c", "import time; time.sleep(2)"]
    code, stdout, stderr = await safe_subprocess_exec(cmd, timeout_seconds=0.1)
    assert code == -1
    assert "timed out" in stderr.lower()
