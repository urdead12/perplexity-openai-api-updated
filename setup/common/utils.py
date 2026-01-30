"""
Common utilities for installation scripts
Shared between Claude Code and OpenCode variants
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Callable


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


class InstallationState:
    """Manages installation state and progress tracking"""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load state from file or create new"""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            'version': '1.0',
            'started': datetime.now().isoformat(),
            'last_updated': None,
            'completed_stages': [],
            'failed_stage': None,
            'rollback_info': {},
            'installation_dir': None
        }

    def save(self):
        """Save current state"""
        self.state['last_updated'] = datetime.now().isoformat()
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def mark_stage_complete(self, stage: str, info: Dict = None):
        """Mark a stage as completed"""
        if stage not in self.state['completed_stages']:
            self.state['completed_stages'].append(stage)
        if info:
            self.state.setdefault('stage_info', {})[stage] = info
        self.save()

    def is_stage_complete(self, stage: str) -> bool:
        """Check if stage is already completed"""
        return stage in self.state['completed_stages']

    def mark_failed(self, stage: str, error: str):
        """Mark stage as failed"""
        self.state['failed_stage'] = stage
        self.state['error'] = error
        self.save()

    def add_rollback_info(self, stage: str, info: Dict):
        """Add rollback information for a stage"""
        self.state['rollback_info'][stage] = info
        self.save()

    def reset(self):
        """Reset state"""
        if self.state_file.exists():
            self.state_file.unlink()
        self.state = self._load_state()


class InstallationStage:
    """Represents a single installation stage with checks and rollback"""

    def __init__(self,
                 name: str,
                 description: str,
                 pre_check: Callable,
                 action: Callable,
                 post_check: Callable,
                 rollback: Optional[Callable] = None,
                 required: bool = True):
        self.name = name
        self.description = description
        self.pre_check = pre_check
        self.action = action
        self.post_check = post_check
        self.rollback = rollback
        self.required = required

    def execute(self, context: Dict) -> bool:
        """Execute this stage"""
        try:
            # Pre-check
            print_stage(f"Pre-check: {self.description}")
            if not self.pre_check(context):
                if self.required:
                    raise Exception(f"Pre-check failed for {self.name}")
                else:
                    print_warning(f"Pre-check failed, skipping optional stage {self.name}")
                    return True

            # Main action
            print_stage(f"Executing: {self.description}")
            rollback_info = self.action(context)
            if rollback_info:
                context['state'].add_rollback_info(self.name, rollback_info)

            # Post-check
            print_stage(f"Post-check: {self.description}")
            if not self.post_check(context):
                raise Exception(f"Post-check failed for {self.name}")

            print_success(f"Completed: {self.description}")
            context['state'].mark_stage_complete(self.name)
            return True

        except Exception as e:
            print_error(f"Failed: {self.description}")
            print_error(f"Error: {str(e)}")
            context['state'].mark_failed(self.name, str(e))
            raise


# Print utilities
def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_stage(text):
    print(f"{Colors.OKBLUE}[STAGE] {text}{Colors.ENDC}")


def print_success(text):
    print(f"{Colors.OKGREEN}[✓] {text}{Colors.ENDC}")


def print_info(text):
    print(f"{Colors.OKCYAN}[→] {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.WARNING}[⚠] {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.FAIL}[✗] {text}{Colors.ENDC}")


def run_command(cmd, check=True, capture_output=False, cwd=None, shell=True):
    """Run a shell command"""
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=shell, check=check,
                                  capture_output=True, text=True, cwd=cwd)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=shell, check=check, cwd=cwd)
            return None
    except subprocess.CalledProcessError as e:
        if capture_output:
            print_error(f"Command output: {e.stderr}")
        raise


# Common installation stages
def check_python_version(min_major=3, min_minor=10) -> bool:
    """Check if Python version meets minimum requirements"""
    version = sys.version_info
    if version.major < min_major or (version.major == min_major and version.minor < min_minor):
        print_error(f"Python {min_major}.{min_minor}+ required, found {version.major}.{version.minor}")
        return False
    print_info(f"Python {version.major}.{version.minor}.{version.micro} detected")
    return True


def check_git_installed() -> bool:
    """Check if git is installed"""
    try:
        run_command("git --version", capture_output=True)
        return True
    except:
        return False


def get_perplexity_token() -> Optional[str]:
    """Get Perplexity session token from environment or user input"""
    token = os.getenv("PERPLEXITY_SESSION_TOKEN")
    if token:
        print_success("Found PERPLEXITY_SESSION_TOKEN in environment")
        return token

    print()
    print_warning("PERPLEXITY_SESSION_TOKEN not found in environment")
    print()
    print("To get your session token:")
    print("1. Log in at https://www.perplexity.ai")
    print("2. Open DevTools (F12) → Application → Cookies")
    print("3. Copy the '__Secure-next-auth.session-token' value")
    print()

    token = input("Enter your Perplexity session token (or press Enter to skip): ").strip()
    if token:
        return token
    return None


def create_venv(install_dir: Path) -> Path:
    """Create a virtual environment"""
    venv_path = install_dir / "venv"
    print_info(f"Creating virtual environment at {venv_path}")
    run_command(f"{sys.executable} -m venv {venv_path}")
    return venv_path


def get_venv_python(venv_path: Path) -> Path:
    """Get path to Python executable in venv"""
    if os.name == 'nt':  # Windows
        return venv_path / "Scripts" / "python.exe"
    else:  # Unix-like
        return venv_path / "bin" / "python"


def install_pip_package(venv_python: Path, package: str):
    """Install a pip package in the virtual environment"""
    print_info(f"Installing {package}")
    run_command(f"{venv_python} -m pip install -q {package}")


def clone_repository(repo_url: str, target_dir: Path, branch: Optional[str] = None):
    """Clone a git repository"""
    print_info(f"Cloning {repo_url}")
    if branch:
        run_command(f"git clone -b {branch} {repo_url} {target_dir}")
    else:
        run_command(f"git clone {repo_url} {target_dir}")


def create_env_file(install_dir: Path, env_vars: Dict[str, str]):
    """Create a .env file with the given variables"""
    env_file = install_dir / ".env"
    print_info(f"Creating .env file at {env_file}")

    with open(env_file, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

    return env_file
