"""
Claude Code + Perplexity Launcher
Checks and starts services using venv, then launches Claude Code
Runs openai_server.py from correct directory with .env
"""

import os
import sys
import time
import socket
import subprocess
import signal
import threading
import shlex
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    import io
    try:
        # Try to set UTF-8 encoding for stdout/stderr
        if sys.stdout.encoding != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)
        if sys.stderr.encoding != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True)
    except (AttributeError, RuntimeError):
        # If wrapping fails, continue without it
        pass

class Colors:
    """ANSI color codes"""
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    OKCYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class LogManager:
    """Manage timestamped log files for services"""

    def __init__(self, install_dir: Path):
        self.install_dir = install_dir
        self.logs_dir = install_dir / "logs"
        self.logs_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_files = {}
        self.tail_processes = []

    def get_log_file(self, service_name: str, stream_type: str = "output") -> tuple:
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
            services = ["Perplexity", "LiteLLM"]

        print()
        print(f"{Colors.OKCYAN}Opening tail windows...{Colors.ENDC}")

        for service in services:
            # Find the combined log file (stdout + stderr will be shown)
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

def print_status(service, status, message=""):
    """Print service status"""
    if status == "running":
        symbol = "✓"
        color = Colors.OKGREEN
    elif status == "starting":
        symbol = "→"
        color = Colors.OKCYAN
    elif status == "stopped":
        symbol = "■"
        color = Colors.WARNING
    else:
        symbol = "✗"
        color = Colors.FAIL

    msg = f"{color}{symbol} {service}{Colors.ENDC}"
    if message:
        msg += f" - {message}"
    print(msg)

def is_port_in_use(port: int) -> bool:
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except OSError:
            return True

def check_service_health(url: str, timeout: int = 2) -> bool:
    """Check if service is responding"""
    import urllib.request
    try:
        urllib.request.urlopen(url, timeout=timeout)
        return True
    except:
        return False

class ServiceMonitor:
    """Monitor services and alert if they go down"""

    def __init__(self, wrapper_process, litellm_process, check_interval: int = 30):
        self.wrapper_process = wrapper_process
        self.litellm_process = litellm_process
        self.check_interval = check_interval
        self.running = True
        self.wrapper_down = False
        self.litellm_down = False
        self.thread = None

    def start(self):
        """Start monitoring in background"""
        if self.wrapper_process is None and self.litellm_process is None:
            return  # Nothing to monitor

        self.thread = threading.Thread(target=self._monitor, daemon=True)
        self.thread.start()

    def stop(self):
        """Stop monitoring"""
        self.running = False

    def _monitor(self):
        """Monitor loop"""
        while self.running:
            try:
                # Check Perplexity Wrapper
                if self.wrapper_process and self.wrapper_process.poll() is None:
                    # Process is running, check health
                    if not check_service_health("http://localhost:8000/health"):
                        if not self.wrapper_down:
                            print()
                            print(f"{Colors.WARNING}⚠ Perplexity Wrapper is not responding{Colors.ENDC}")
                            self.wrapper_down = True
                    else:
                        if self.wrapper_down:
                            print()
                            print(f"{Colors.OKGREEN}✓ Perplexity Wrapper recovered{Colors.ENDC}")
                            self.wrapper_down = False
                else:
                    # Process died
                    if self.wrapper_process and not self.wrapper_down:
                        print()
                        print(f"{Colors.FAIL}✗ Perplexity Wrapper process died (code: {self.wrapper_process.poll()}){Colors.ENDC}")
                        self.wrapper_down = True

                # Check LiteLLM Proxy
                if self.litellm_process and self.litellm_process.poll() is None:
                    # Process is running, check health
                    if not check_service_health("http://localhost:8080/health/readiness"):
                        if not self.litellm_down:
                            print()
                            print(f"{Colors.WARNING}⚠ LiteLLM Proxy is not responding{Colors.ENDC}")
                            self.litellm_down = True
                    else:
                        if self.litellm_down:
                            print()
                            print(f"{Colors.OKGREEN}✓ LiteLLM Proxy recovered{Colors.ENDC}")
                            self.litellm_down = False
                else:
                    # Process died
                    if self.litellm_process and not self.litellm_down:
                        print()
                        print(f"{Colors.FAIL}✗ LiteLLM Proxy process died (code: {self.litellm_process.poll()}){Colors.ENDC}")
                        self.litellm_down = True

                time.sleep(self.check_interval)
            except Exception as e:
                # Don't crash the monitor on errors
                pass

def fetch_available_models(base_url: str = "http://localhost:8000") -> list:
    """Fetch available models from the OpenAI-compatible API"""
    import urllib.request
    import json
    try:
        url = f"{base_url}/v1/models"
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            models = [m["id"] for m in data.get("data", [])]
            return sorted(models)
    except Exception as e:
        print(f"{Colors.WARNING}Warning: Could not fetch models: {e}{Colors.ENDC}")
        return []

def read_litellm_models(install_dir: Path) -> list:
    """Read available models from litellm config"""
    config_file = install_dir / "litellm_config.yaml"

    if not config_file.exists():
        return []

    try:
        import yaml
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f) or {}

        model_list = config.get("model_list", [])
        return [m.get("model_name") for m in model_list if m.get("model_name")]
    except ImportError:
        return []
    except Exception as e:
        print(f"{Colors.WARNING}Warning: Could not read models: {e}{Colors.ENDC}")
        return []

def update_litellm_config(install_dir: Path, models: list) -> None:
    """Update litellm config with discovered models"""
    import yaml

    config_file = install_dir / "litellm_config.yaml"

    if not config_file.exists():
        print(f"{Colors.WARNING}Warning: Config file not found{Colors.ENDC}")
        return

    try:
        # Read current config
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f) or {}

        # Build model list for litellm
        model_list = []
        for model_id in models:
            model_entry = {
                "model_name": model_id.replace("/", "-").replace("perplexity-", ""),
                "litellm_params": {
                    "model": f"openai/{model_id}",
                    "api_base": "http://localhost:8000/v1",
                    "api_key": "dummy"
                }
            }
            model_list.append(model_entry)

        # Update config
        config["model_list"] = model_list
        if "litellm_settings" not in config:
            config["litellm_settings"] = {}
        config["litellm_settings"]["set_verbose"] = False
        config["litellm_settings"]["drop_params"] = True

        # Write updated config
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        print(f"{Colors.OKGREEN}✓ Updated litellm config with {len(models)} model(s){Colors.ENDC}")
        for model in models[:5]:
            print(f"  - {model}")
        if len(models) > 5:
            print(f"  ... and {len(models) - 5} more")
    except ImportError:
        print(f"{Colors.WARNING}Warning: PyYAML not installed, cannot update config{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.WARNING}Warning: Could not update config: {e}{Colors.ENDC}")

def get_install_dir() -> Path:
    """Get installation directory"""
    install_dir = Path.home() / ".claude-perplexity"
    if not install_dir.exists():
        print(f"{Colors.FAIL}Error: Installation directory not found{Colors.ENDC}")
        print(f"Expected: {install_dir}")
        print("Run install_claude_perplexity.py first")
        sys.exit(1)
    return install_dir



def find_process_on_port(port: int) -> Optional[int]:
    """Find process ID using a port (Windows-compatible)"""
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

def start_perplexity_wrapper(install_dir: Path, log_manager: 'LogManager' = None) -> subprocess.Popen:
    """Start the Perplexity wrapper service"""
    print_status("Perplexity Wrapper", "starting", "Starting on port 8000...")

    # Wrapper directory
    wrapper_dir = install_dir / "perplexity-openai-api-updated"
    server_file = wrapper_dir / "openai_server.py"

    if not server_file.exists():
        print(f"{Colors.FAIL}Error: openai_server.py not found{Colors.ENDC}")
        print(f"Expected: {server_file}")
        print(f"Wrapper dir: {wrapper_dir}")
        sys.exit(1)

    # Check if .env exists in wrapper dir
    env_file = wrapper_dir / ".env"
    if not env_file.exists():
        print(f"{Colors.WARNING}Warning: .env not found in {wrapper_dir}{Colors.ENDC}")
        print("Server may fail without session token")

    print(f"{Colors.OKCYAN}→ Running: {sys.executable} openai_server.py{Colors.ENDC}")
    print(f"{Colors.OKCYAN}→ Working dir: {wrapper_dir}{Colors.ENDC}")

    # Build command - use current Python interpreter (which is the venv if activated)
    cmd = [sys.executable, "openai_server.py"]

    # Create an environment for the subprocess by copying the current one
    env = os.environ.copy()
    # Force UTF-8 encoding to prevent Unicode errors
    env["PYTHONIOENCODING"] = "utf-8"

    # Print separator
    print()
    print(f"{Colors.OKGREEN}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}Perplexity Wrapper Output:{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{'=' * 60}{Colors.ENDC}")

    # Setup logging if log_manager provided
    stdout_file = None
    stderr_file = None
    if log_manager:
        _, stdout_file = log_manager.get_log_file("Perplexity", "stdout")
        _, stderr_file = log_manager.get_log_file("Perplexity", "stderr")

    # Start the process from wrapper directory (where .env is)
    if os.name == 'nt':
        # Windows: Create new process group
        process = subprocess.Popen(
            cmd,
            cwd=str(wrapper_dir),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            env=env,
            stdout=stdout_file,
            stderr=stderr_file
        )
    else:
        # Unix: Use preexec_fn
        process = subprocess.Popen(
            cmd,
            cwd=str(wrapper_dir),
            preexec_fn=os.setsid,
            env=env,
            stdout=stdout_file,
            stderr=stderr_file
        )

    # Wait for service to be ready
    print(f"\n{Colors.OKCYAN}→ Waiting for health check...{Colors.ENDC}")
    max_wait = 30
    for i in range(max_wait):
        # Check if process died
        if process.poll() is not None:
            print_status("Perplexity Wrapper", "error", f"Process exited (code: {process.returncode})")
            sys.exit(1)

        if check_service_health("http://localhost:8000/health"):
            print(f"{Colors.OKGREEN}✓ Service is healthy{Colors.ENDC}")
            return process

        # Show progress every 5 seconds
        if (i + 1) % 5 == 0:
            print(f"{Colors.OKCYAN}  Waiting {i + 1}s... (timeout in {max_wait - i}s){Colors.ENDC}")

        time.sleep(1)

    # If health check fails, check if port is at least listening
    if is_port_in_use(8000):
        print(f"{Colors.WARNING}⚠ Health check failed but port is listening{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✓ Assuming service is ready{Colors.ENDC}")
        return process

    print_status("Perplexity Wrapper", "error", "Failed to start (timeout)")
    process.kill()
    sys.exit(1)

def start_litellm_proxy(install_dir: Path, log_manager: 'LogManager' = None) -> subprocess.Popen:
    """Start the LiteLLM proxy service"""
    print_status("LiteLLM Proxy", "starting", "Starting on port 8080...")

    config_file = install_dir / "litellm_config.yaml"
    if not config_file.exists():
        print(f"{Colors.FAIL}Error: LiteLLM config not found{Colors.ENDC}")
        print(f"Expected: {config_file}")
        sys.exit(1)

    print(f"{Colors.OKCYAN}→ Running: litellm --config {config_file} --port 8080{Colors.ENDC}")

    # Build command - use shell to inherit venv environment
    cmd = f'litellm --config "{config_file}" --port 8080'

    # Create an environment for the subprocess by copying the current one
    env = os.environ.copy()
    # Force UTF-8 encoding to prevent Unicode errors in litellm banner
    env["PYTHONIOENCODING"] = "utf-8"

    # Setup logging if log_manager provided
    stdout_file = None
    stderr_file = None
    if log_manager:
        _, stdout_file = log_manager.get_log_file("LiteLLM", "stdout")
        _, stderr_file = log_manager.get_log_file("LiteLLM", "stderr")

    # Print separator
    print()
    print(f"{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}LiteLLM Proxy Output:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'=' * 60}{Colors.ENDC}")

    # Start the process with shell to find litellm in venv PATH
    if os.name == 'nt':
        process = subprocess.Popen(
            cmd,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            shell=True,
            env=env,
            stdout=stdout_file,
            stderr=stderr_file
        )
    else:
        process = subprocess.Popen(
            cmd,
            preexec_fn=os.setsid,
            shell=True,
            env=env,
            stdout=stdout_file,
            stderr=stderr_file
        )

    # Wait for service to be ready
    print(f"\n{Colors.OKCYAN}→ Waiting for health check...{Colors.ENDC}")
    max_wait = 30
    for i in range(max_wait):
        # Check if process died
        if process.poll() is not None:
            print_status("LiteLLM Proxy", "error", f"Process exited (code: {process.returncode})")
            sys.exit(1)

        if check_service_health("http://localhost:8080/health/readiness"):
            print(f"{Colors.OKGREEN}✓ Service is healthy{Colors.ENDC}")
            return process

        # Show progress every 5 seconds
        if (i + 1) % 5 == 0:
            print(f"{Colors.OKCYAN}  Waiting {i + 1}s... (timeout in {max_wait - i}s){Colors.ENDC}")

        time.sleep(1)

    # If health check fails, check if port is at least listening
    if is_port_in_use(8080):
        print(f"{Colors.WARNING}⚠ Health check failed but port is listening{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✓ Assuming service is ready{Colors.ENDC}")
        return process

    print_status("LiteLLM Proxy", "error", "Failed to start (timeout)")
    process.kill()
    sys.exit(1)

def check_and_start_services(install_dir: Path) -> Tuple[Optional[subprocess.Popen], Optional[subprocess.Popen], LogManager]:
    """Check if services are running and start if needed"""
    wrapper_process = None
    litellm_process = None

    # Create log manager
    log_manager = LogManager(install_dir)

    print()
    print(f"{Colors.BOLD}Service Status Check{Colors.ENDC}")
    print()

    # Check Perplexity wrapper (port 8000)
    if is_port_in_use(8000):
        if check_service_health("http://localhost:8000/health"):
            print_status("Perplexity Wrapper", "running", "Already running on port 8000")
        else:
            print(f"{Colors.WARNING}Port 8000 in use but not responding{Colors.ENDC}")
            pid = find_process_on_port(8000)
            if pid:
                print(f"Process {pid} is using port 8000")
                print("Please stop it manually or use a different port")
                sys.exit(1)
    else:
        wrapper_process = start_perplexity_wrapper(install_dir, log_manager)

    # Fetch available models and update litellm config
    print()
    print(f"{Colors.BOLD}Discovering Models{Colors.ENDC}")
    print()
    print(f"{Colors.OKCYAN}→ Fetching available models from Perplexity...{Colors.ENDC}")
    time.sleep(1)  # Give server a moment to settle

    models = fetch_available_models()
    if models:
        print(f"{Colors.OKGREEN}✓ Found {len(models)} model(s){Colors.ENDC}")
        update_litellm_config(install_dir, models)
    else:
        print(f"{Colors.WARNING}⚠ No models found, using default config{Colors.ENDC}")

    # Check LiteLLM proxy (port 8080)
    print()
    if is_port_in_use(8080):
        if check_service_health("http://localhost:8080/health/readiness"):
            print_status("LiteLLM Proxy", "running", "Already running on port 8080")
        else:
            print(f"{Colors.WARNING}Port 8080 in use but not responding{Colors.ENDC}")
            pid = find_process_on_port(8080)
            if pid:
                print(f"Process {pid} is using port 8080")
                print("Please stop it manually or use a different port")
                sys.exit(1)
    else:
        litellm_process = start_litellm_proxy(install_dir, log_manager)

    return wrapper_process, litellm_process, log_manager

def check_claude_installed() -> bool:
    """Check if Claude Code is installed"""
    try:
        result = subprocess.run(
            "claude --version",
            shell=True,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False

def launch_claude(model: str = None, extra_args: list = None):
    """Launch Claude Code with Perplexity backend"""
    print()
    print(f"{Colors.OKGREEN}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{Colors.BOLD}Launching Claude Code with Perplexity Backend{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print()

    # Set environment variables for Claude
    env = os.environ.copy()
    env["ANTHROPIC_BASE_URL"] = "http://localhost:8080"
    env["ANTHROPIC_API_KEY"] = "dummy"

    # Set model (use provided or default)
    if model:
        env["ANTHROPIC_MODEL"] = model
    elif "ANTHROPIC_MODEL" not in env:
        env["ANTHROPIC_MODEL"] = "claude-sonnet-4.5"

    print(f"{Colors.OKCYAN}Environment:{Colors.ENDC}")
    print(f"  ANTHROPIC_BASE_URL = {env['ANTHROPIC_BASE_URL']}")
    print(f"  ANTHROPIC_MODEL = {env.get('ANTHROPIC_MODEL', 'default')}")
    print()

    # Check if Claude is installed
    if not check_claude_installed():
        print(f"{Colors.WARNING}Warning: Claude Code CLI not found{Colors.ENDC}")
        print("Make sure Claude Code is installed and 'claude' is in your PATH")
        print()
        print("You can still use the services with other tools:")
        print(f"  Perplexity Wrapper: http://localhost:8000")
        print(f"  LiteLLM Proxy: http://localhost:8080")
        print()
        input("Press Enter to exit...")
        return

    try:
        # Launch Claude Code
        print(f"{Colors.OKCYAN}Starting Claude Code...{Colors.ENDC}")
        if extra_args:
            print(f"{Colors.OKCYAN}With arguments: {' '.join(extra_args)}{Colors.ENDC}")
        print()

        # On Windows, use shell=True and properly quote arguments
        # On Unix, use list form directly
        if os.name == 'nt':
            cmd = "claude"
            if extra_args:
                # Properly quote arguments for shell
                quoted_args = " ".join(shlex.quote(arg) for arg in extra_args)
                cmd += " " + quoted_args
            subprocess.run(cmd, shell=True, env=env)
        else:
            cmd = ["claude"]
            if extra_args:
                cmd.extend(extra_args)
            subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print()
        print(f"{Colors.WARNING}Claude Code session ended{Colors.ENDC}")

def cleanup_processes(wrapper_process, litellm_process):
    """Clean up spawned processes"""
    print()
    print(f"{Colors.OKCYAN}Cleaning up services...{Colors.ENDC}")

    if wrapper_process:
        try:
            if os.name == 'nt':
                wrapper_process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                wrapper_process.terminate()
            wrapper_process.wait(timeout=5)
            print_status("Perplexity Wrapper", "stopped", "Stopped")
        except:
            wrapper_process.kill()

    if litellm_process:
        try:
            if os.name == 'nt':
                litellm_process.send_signal(signal.CTRL_BREAK_EVENT)
            else:
                litellm_process.terminate()
            litellm_process.wait(timeout=5)
            print_status("LiteLLM Proxy", "stopped", "Stopped")
        except:
            litellm_process.kill()

def start_services_only(install_dir: Path) -> Tuple[subprocess.Popen, subprocess.Popen, LogManager]:
    """Start services and keep them running"""
    print()
    print(f"{Colors.BOLD}Starting Perplexity Services{Colors.ENDC}")
    print()
    print(f"{Colors.OKCYAN}→ Install directory: {install_dir}{Colors.ENDC}")

    # Check wrapper directory
    wrapper_dir = install_dir / "perplexity-openai-api-updated"
    if not wrapper_dir.exists():
        print(f"{Colors.FAIL}Error: Wrapper not found at {wrapper_dir}{Colors.ENDC}")
        print("Run install_claude_perplexity.py first")
        sys.exit(1)

    print(f"{Colors.OKCYAN}→ Wrapper directory: {wrapper_dir}{Colors.ENDC}")

    # Check and start services
    wrapper_process, litellm_process, log_manager = check_and_start_services(install_dir)

    print()
    print(f"{Colors.OKGREEN}Services are running!{Colors.ENDC}")
    print(f"  Perplexity Wrapper: http://localhost:8000")
    print(f"  LiteLLM Proxy: http://localhost:8080")
    print()
    print(f"{Colors.OKCYAN}Press Ctrl+C to stop services...{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Logs are saved in: {log_manager.logs_dir}{Colors.ENDC}")
    print()

    # Open tail windows to show output
    services_to_tail = []
    if wrapper_process:
        services_to_tail.append("Perplexity")
    if litellm_process:
        services_to_tail.append("LiteLLM")

    if services_to_tail:
        log_manager.open_tail_windows(services_to_tail)

    return wrapper_process, litellm_process, log_manager

def launch_claude_only(install_dir: Path, extra_args: list = None) -> None:
    """Launch Claude Code with existing services"""
    print()
    print(f"{Colors.BOLD}Launching Claude Code with Perplexity Backend{Colors.ENDC}")
    print()

    # Check if services are running
    if not is_port_in_use(8000) or not is_port_in_use(8080):
        print(f"{Colors.WARNING}Warning: Services may not be running{Colors.ENDC}")
        if not is_port_in_use(8000):
            print(f"  Perplexity Wrapper (port 8000): Not running")
        if not is_port_in_use(8080):
            print(f"  LiteLLM Proxy (port 8080): Not running")
        print()
        response = input(f"{Colors.WARNING}Continue anyway? (y/n): {Colors.ENDC}")
        if response.lower() != 'y':
            return

    # Read available models from litellm config
    print()
    available_models = read_litellm_models(install_dir)

    if available_models:
        print(f"{Colors.BOLD}Available Models:{Colors.ENDC}")
        for i, model in enumerate(available_models, 1):
            print(f"  {i}. {model}")
        print()

        # Ask user to select a model
        while True:
            try:
                choice = input(f"{Colors.OKCYAN}Select model (1-{len(available_models)}) or press Enter for first: {Colors.ENDC}").strip()
                if not choice:
                    selected_model = available_models[0]
                    break
                idx = int(choice) - 1
                if 0 <= idx < len(available_models):
                    selected_model = available_models[idx]
                    break
                print(f"{Colors.FAIL}Invalid selection{Colors.ENDC}")
            except ValueError:
                print(f"{Colors.FAIL}Please enter a valid number{Colors.ENDC}")

        print()
        print(f"{Colors.OKGREEN}✓ Selected model: {selected_model}{Colors.ENDC}")
        print()

        # Launch Claude with selected model
        launch_claude(selected_model, extra_args)
    else:
        print(f"{Colors.WARNING}⚠ No models found in config{Colors.ENDC}")
        print()
        launch_claude(extra_args=extra_args)

def main():
    """Main launcher routine"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Claude Code + Perplexity Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch_claude_perplexity.py
    Start services and launch Claude (opens tail windows on Windows)

  python launch_claude_perplexity.py --services-only
    Start services only (opens tail windows on Windows)

  python launch_claude_perplexity.py --claude-only
    Launch Claude with existing services

  python launch_claude_perplexity.py -- --help
    Launch Claude with --help flag

  python launch_claude_perplexity.py -- /path/to/file.md
    Launch Claude with a file

  python launch_claude_perplexity.py --claude-only -- -m "Start coding"
    Launch Claude with model selection and message

Features:
  • Automatic log file creation (timestamped in ~/.claude-perplexity/logs/)
  • Real-time tail windows for service output (Windows PowerShell)
  • Service health monitoring with auto-alerts
  • Model discovery and configuration
        """
    )
    parser.add_argument(
        "--services-only",
        action="store_true",
        help="Start services only and keep them running"
    )
    parser.add_argument(
        "--claude-only",
        action="store_true",
        help="Launch Claude Code with existing services (don't start services)"
    )

    # Parse known args and capture unknown args to pass to claude
    args, extra_args = parser.parse_known_args()

    # Remove '--' separator if present in extra_args
    if extra_args and extra_args[0] == '--':
        extra_args = extra_args[1:]

    wrapper_process = None
    litellm_process = None
    monitor = None
    log_manager = None

    try:
        install_dir = get_install_dir()

        if args.claude_only:
            # Only launch Claude Code
            launch_claude_only(install_dir, extra_args)
        elif args.services_only:
            # Only start services
            wrapper_process, litellm_process, log_manager = start_services_only(install_dir)

            # Start monitoring
            monitor = ServiceMonitor(wrapper_process, litellm_process, check_interval=30)
            monitor.start()

            # Keep running until interrupted
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print()
                print(f"{Colors.WARNING}Stopping services...{Colors.ENDC}")
        else:
            # Default: Start services then launch Claude
            print()
            print(f"{Colors.BOLD}Claude Code + Perplexity Launcher{Colors.ENDC}")
            print()
            print(f"{Colors.OKCYAN}→ Install directory: {install_dir}{Colors.ENDC}")

            # Check wrapper directory
            wrapper_dir = install_dir / "perplexity-openai-api-updated"
            if not wrapper_dir.exists():
                print(f"{Colors.FAIL}Error: Wrapper not found at {wrapper_dir}{Colors.ENDC}")
                print("Run install_claude_perplexity.py first")
                sys.exit(1)

            print(f"{Colors.OKCYAN}→ Wrapper directory: {wrapper_dir}{Colors.ENDC}")

            # Check and start services
            wrapper_process, litellm_process, log_manager = check_and_start_services(install_dir)

            # Start monitoring
            monitor = ServiceMonitor(wrapper_process, litellm_process, check_interval=30)
            monitor.start()

            # Open tail windows to show output
            services_to_tail = []
            if wrapper_process:
                services_to_tail.append("Perplexity")
            if litellm_process:
                services_to_tail.append("LiteLLM")

            if services_to_tail:
                log_manager.open_tail_windows(services_to_tail)

            # Launch Claude Code
            launch_claude(extra_args=extra_args)

    except KeyboardInterrupt:
        print()
        print(f"{Colors.WARNING}Interrupted by user{Colors.ENDC}")
    except Exception as e:
        print()
        print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Stop monitoring
        if monitor:
            monitor.stop()

        # Clean up only if we started the processes
        cleanup_processes(wrapper_process, litellm_process)

        # Close log files
        if log_manager:
            log_manager.close_all()
            print(f"{Colors.OKCYAN}Logs saved to: {log_manager.logs_dir}{Colors.ENDC}")

        print()
        print(f"{Colors.OKGREEN}Done{Colors.ENDC}")

if __name__ == "__main__":
    main()
