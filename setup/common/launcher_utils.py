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
import threading
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

from .utils import Colors, print_success, print_info, print_warning, print_error


class LogManager:
    """Manage timestamped log files for services with tail window support"""

    def __init__(self, install_dir: Path):
        self.install_dir = install_dir
        self.logs_dir = install_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_files = {}
        self.tail_processes = []

    def get_log_file(self, service_name: str, stream_type: str = "stdout") -> tuple:
        """Get or create a log file for a service

        Returns: (file_path, file_handle)
        """
        key = f"{service_name}_{stream_type}"

        if key not in self.log_files:
            log_file = self.logs_dir / f"{self.timestamp}_{service_name}_{stream_type}.log"
            file_handle = open(log_file, 'w', buffering=1)
            self.log_files[key] = (log_file, file_handle)

            # Print to console
            print(f"{Colors.OKCYAN}→ {service_name} {stream_type}: {log_file}{Colors.ENDC}")

        return self.log_files[key]

    def open_tail_windows(self, services: list = None):
        """Open tail windows for services (Windows/PowerShell only)

        services: list of service names (e.g., ["Perplexity", "LiteLLM"])
        """
        if os.name != 'nt':
            print(f"{Colors.WARNING}⚠ Tail windows only supported on Windows{Colors.ENDC}")
            return

        if services is None:
            services = []

        print()
        print(f"{Colors.OKCYAN}Opening tail windows...{Colors.ENDC}")

        for service in services:
            # Find the log file for stdout
            log_file = None
            for file_path, _ in self.log_files.values():
                if service in str(file_path) and "stdout" in str(file_path):
                    log_file = file_path
                    break

            if log_file and log_file.exists():
                self._open_tail_window(service, log_file)
            else:
                print(f"{Colors.WARNING}  ⚠ No log file found for {service}{Colors.ENDC}")

    def _open_tail_window(self, service_name: str, log_file: Path):
        """Open a PowerShell window to tail a log file"""
        try:
            # Create PowerShell command to follow the log file
            ps_command = (
                f"$title = '{service_name} - Logs'; "
                f"$host.UI.RawUI.WindowTitle = $title; "
                f"Write-Host '{service_name} Output (live tail):' -ForegroundColor Cyan; "
                f"Write-Host '================================================' -ForegroundColor Cyan; "
                f"Get-Content -Path '{log_file}' -Tail 50 -Wait; "
                f"Write-Host 'Window will close when service stops' -ForegroundColor Yellow"
            )

            # Open PowerShell with the tail command
            process = subprocess.Popen(
                [
                    "powershell",
                    "-NoExit",
                    "-Command",
                    ps_command
                ],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )

            self.tail_processes.append(process)
            print(f"{Colors.OKGREEN}✓ Opened tail window for {service_name}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.WARNING}⚠ Could not open tail window for {service_name}: {e}{Colors.ENDC}")

    def close_all(self):
        """Close all open log files and tail windows"""
        for file_path, file_handle in self.log_files.values():
            try:
                file_handle.close()
            except:
                pass

        # Close tail windows
        for process in self.tail_processes:
            try:
                process.terminate()
            except:
                pass


class ServiceMonitor:
    """Monitor services and alert if they go down"""

    def __init__(self, processes: dict, check_interval: int = 30):
        """
        Args:
            processes: dict of service_name -> (process, health_url)
            check_interval: seconds between health checks
        """
        self.processes = processes
        self.check_interval = check_interval
        self.running = True
        self.down_services = set()
        self.thread = None

    def start(self):
        """Start monitoring in background"""
        if not self.processes:
            return

        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop monitoring"""
        self.running = False

    def _monitor(self):
        """Monitor loop"""
        while self.running:
            try:
                for service_name, (process, health_url) in self.processes.items():
                    # Check if process is still running
                    if process and process.poll() is None:
                        # Process is running, check health
                        if health_url and not check_service_health(health_url):
                            if service_name not in self.down_services:
                                print()
                                print(f"{Colors.WARNING}⚠ {service_name} is not responding{Colors.ENDC}")
                                self.down_services.add(service_name)
                        else:
                            if service_name in self.down_services:
                                print()
                                print(f"{Colors.OKGREEN}✓ {service_name} recovered{Colors.ENDC}")
                                self.down_services.remove(service_name)
                    else:
                        # Process died
                        if process and service_name not in self.down_services:
                            print()
                            print(f"{Colors.FAIL}✗ {service_name} process died (code: {process.poll()}){Colors.ENDC}")
                            self.down_services.add(service_name)

                time.sleep(self.check_interval)
            except Exception:
                # Don't crash the monitor on errors
                pass


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
    log_manager: Optional['LogManager'] = None
) -> subprocess.Popen:
    """Start the Perplexity OpenAI server

    Args:
        repo_dir: Path to the repository directory
        venv_python: Path to the virtual environment Python executable
        log_manager: Optional LogManager for handling logs

    Returns:
        subprocess.Popen: The server process
    """
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
    stdout_file = None
    stderr_file = None
    if log_manager:
        _, stdout_file = log_manager.get_log_file("Perplexity", "stdout")
        _, stderr_file = log_manager.get_log_file("Perplexity", "stderr")

    # Start process
    if os.name == 'nt':
        process = subprocess.Popen(
            cmd,
            cwd=str(repo_dir),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            env=env,
            stdout=stdout_file,
            stderr=stderr_file
        )
    else:
        process = subprocess.Popen(
            cmd,
            cwd=str(repo_dir),
            preexec_fn=os.setsid,
            env=env,
            stdout=stdout_file,
            stderr=stderr_file
        )

    # Wait for server to be ready
    print_info("Waiting for server to start...")
    max_wait = 30
    for i in range(max_wait):
        # Check if process died
        if process.poll() is not None:
            print_error(f"Server process exited with code {process.returncode}")
            if log_manager:
                print_error(f"Check logs in: {log_manager.logs_dir}")
            raise RuntimeError("Server failed to start")

        # Check if server is responding
        if check_service_health("http://localhost:8000/health"):
            print_success("Perplexity OpenAI Server is running")
            return process

        # Show progress every 5 seconds
        if (i + 1) % 5 == 0:
            print(f"{Colors.OKCYAN}  Waiting {i + 1}s... (timeout in {max_wait - i}s){Colors.ENDC}")

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
