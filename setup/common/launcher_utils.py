"""
Common utilities for launcher scripts
Shared between Claude Code and OpenCode variants
"""

import os
import sys
import time
import socket
import subprocess
import signal
from pathlib import Path
from typing import Optional, Tuple

from .utils import Colors, print_success, print_info, print_warning, print_error


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except OSError:
            return True


def check_service_health(url: str, timeout: int = 2) -> bool:
    """Check if a service is responding"""
    import urllib.request
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except:
        return False


def find_process_on_port(port: int) -> Optional[int]:
    """Find process ID using a port (cross-platform)"""
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(
                f'netstat -ano | findstr :{port}',
                shell=True,
                capture_output=True,
                text=True
            )
            for line in result.stdout.split('\n'):
                if 'LISTENING' in line:
                    parts = line.split()
                    if parts:
                        return int(parts[-1])
        else:  # Unix-like
            result = subprocess.run(
                f'lsof -ti:{port}',
                shell=True,
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                return int(result.stdout.strip().split()[0])
    except:
        pass
    return None


def start_perplexity_server(
    repo_dir: Path,
    venv_python: Path,
    log_file: Optional[Path] = None
) -> subprocess.Popen:
    """Start the Perplexity OpenAI server"""
    print()
    print_info("Starting Perplexity OpenAI Server on port 8000...")

    server_file = repo_dir / "openai_server.py"
    if not server_file.exists():
        raise FileNotFoundError(f"Server file not found: {server_file}")

    # Check for .env file
    env_file = repo_dir / ".env"
    if not env_file.exists():
        print_warning(f".env file not found at {env_file}")
        print_warning("Server may fail without PERPLEXITY_SESSION_TOKEN")

    # Build command
    cmd = [str(venv_python), "openai_server.py"]

    # Setup environment
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    # Setup output
    stdout = log_file.open('w') if log_file else None
    stderr = stdout

    # Start process
    if os.name == 'nt':
        process = subprocess.Popen(
            cmd,
            cwd=str(repo_dir),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            env=env,
            stdout=stdout,
            stderr=stderr
        )
    else:
        process = subprocess.Popen(
            cmd,
            cwd=str(repo_dir),
            preexec_fn=os.setsid,
            env=env,
            stdout=stdout,
            stderr=stderr
        )

    # Wait for server to be ready
    print_info("Waiting for server to start...")
    max_wait = 30
    for i in range(max_wait):
        # Check if process died
        if process.poll() is not None:
            print_error(f"Server process exited with code {process.returncode}")
            raise RuntimeError("Server failed to start")

        # Check if server is responding
        if check_service_health("http://localhost:8000/health"):
            print_success("Perplexity OpenAI Server is running")
            return process

        time.sleep(1)

    # Timeout
    if is_port_in_use(8000):
        print_warning("Port 8000 is in use but health check failed")
        print_success("Assuming server is ready")
        return process

    raise TimeoutError("Server failed to start within 30 seconds")


def stop_process(process: subprocess.Popen, name: str = "Process"):
    """Stop a process gracefully"""
    if not process:
        return

    print_info(f"Stopping {name}...")
    try:
        if os.name == 'nt':
            process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            process.terminate()

        process.wait(timeout=5)
        print_success(f"{name} stopped")
    except:
        process.kill()
        print_warning(f"{name} force killed")


def fetch_available_models(base_url: str = "http://localhost:8000") -> list:
    """Fetch available models from the Perplexity OpenAI server"""
    import urllib.request
    import json

    try:
        url = f"{base_url}/v1/models"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            models = [m["id"] for m in data.get("data", [])]
            return sorted(models)
    except Exception as e:
        print_warning(f"Could not fetch models: {e}")
        return []


def get_install_dir(variant: str = "perplexity") -> Path:
    """Get the installation directory for a variant"""
    install_dir = Path.home() / f".{variant}-perplexity"
    if not install_dir.exists():
        raise FileNotFoundError(
            f"Installation directory not found: {install_dir}\n"
            f"Please run the installer first"
        )
    return install_dir
