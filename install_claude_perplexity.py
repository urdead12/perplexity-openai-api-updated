"""
Claude Code + Perplexity Integration Installer
Smart staged installation with state tracking, validation, and rollback
Uses: https://github.com/urdead12/perplexity-openai-api-updated
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Callable

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class InstallationState:
    """Manages installation state and progress"""

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
    """Represents a single installation stage"""

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
    """Run a command"""
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

# Stage 1: Python Version Check
def stage1_pre_check(ctx):
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print_error(f"Python 3.10+ required, found {version.major}.{version.minor}")
        return False
    print_info(f"Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def stage1_action(ctx):
    """Store Python info"""
    ctx['python_version'] = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ctx['python_path'] = sys.executable
    return None

def stage1_post_check(ctx):
    """Verify Python info stored"""
    return 'python_version' in ctx and 'python_path' in ctx

# Stage 2: Check Git
def stage2_pre_check(ctx):
    """Git is optional"""
    return True

def stage2_action(ctx):
    """Check for git"""
    try:
        run_command("git --version", capture_output=True)
        ctx['has_git'] = True
        print_info("Git is available")
    except:
        ctx['has_git'] = False
        print_warning("Git not found - will use pip install from GitHub")
    return None

def stage2_post_check(ctx):
    return 'has_git' in ctx

# Stage 3: Create Installation Directory
def stage3_pre_check(ctx):
    return True

def stage3_action(ctx):
    install_dir = Path.home() / ".claude-perplexity"
    install_dir.mkdir(exist_ok=True)
    ctx['install_dir'] = install_dir
    ctx['state'].state['installation_dir'] = str(install_dir)
    ctx['state'].save()
    print_info(f"Installation directory: {install_dir}")
    return {'created_dir': not install_dir.exists()}

def stage3_post_check(ctx):
    return ctx['install_dir'].exists() and ctx['install_dir'].is_dir()

def stage3_rollback(ctx):
    """Remove installation directory if we created it"""
    rollback = ctx['state'].state['rollback_info'].get('install_dir_setup', {})
    if rollback.get('created_dir'):
        shutil.rmtree(ctx['install_dir'], ignore_errors=True)

# Stage 4: Create Virtual Environment
def stage4_pre_check(ctx):
    return ctx['install_dir'].exists()

def stage4_action(ctx):
    venv_dir = ctx['install_dir'] / "venv"

    if venv_dir.exists():
        print_warning("Virtual environment exists")
        user_input = input("Recreate? (y/N): ").strip().lower()
        if user_input == 'y':
            shutil.rmtree(venv_dir)
            print_info("Removed old venv")
        else:
            print_info("Using existing venv")
            ctx['venv_dir'] = venv_dir

            # Store paths to venv executables
            if os.name == 'nt':
                ctx['venv_python'] = venv_dir / "Scripts" / "python.exe"
                ctx['venv_pip'] = venv_dir / "Scripts" / "pip.exe"
            else:
                ctx['venv_python'] = venv_dir / "bin" / "python"
                ctx['venv_pip'] = venv_dir / "bin" / "pip"

            return {'created_venv': False}

    print_info("Creating virtual environment...")
    run_command(f'"{sys.executable}" -m venv "{venv_dir}"')
    ctx['venv_dir'] = venv_dir

    # Store paths to venv executables
    if os.name == 'nt':
        ctx['venv_python'] = venv_dir / "Scripts" / "python.exe"
        ctx['venv_pip'] = venv_dir / "Scripts" / "pip.exe"
    else:
        ctx['venv_python'] = venv_dir / "bin" / "python"
        ctx['venv_pip'] = venv_dir / "bin" / "pip"

    return {'created_venv': True, 'venv_dir': str(venv_dir)}

def stage4_post_check(ctx):
    return (ctx['venv_dir'].exists() and 
            ctx['venv_python'].exists() and 
            ctx['venv_pip'].exists())

def stage4_rollback(ctx):
    rollback = ctx['state'].state['rollback_info'].get('venv_setup', {})
    if rollback.get('created_venv'):
        shutil.rmtree(ctx['venv_dir'], ignore_errors=True)

# Stage 5: Upgrade pip in venv
def stage5_pre_check(ctx):
    return ctx['venv_pip'].exists()

def stage5_action(ctx):
    print_info("Upgrading pip in virtual environment...")
    run_command(f'"{ctx["venv_pip"]}" install --upgrade pip')
    return None

def stage5_post_check(ctx):
    try:
        version = run_command(f'"{ctx["venv_pip"]}" --version', capture_output=True)
        print_info(f"pip version: {version}")
        return True
    except:
        return False

# Stage 6: Clone Perplexity Wrapper (UPDATED)
def stage6_pre_check(ctx):
    return ctx.get('has_git', False)

def stage6_action(ctx):
    print_info("Cloning Perplexity OpenAI wrapper...")

    wrapper_dir = ctx['install_dir'] / "perplexity-openai-api-updated"

    if wrapper_dir.exists():
        print_info("Wrapper directory exists, pulling latest...")
        run_command('git pull', cwd=str(wrapper_dir))
    else:
        print_info("Cloning from urdead12/perplexity-openai-api-updated...")
        run_command(
            f'git clone https://github.com/urdead12/perplexity-openai-api-updated.git "{wrapper_dir}"'
        )

    ctx['wrapper_dir'] = wrapper_dir
    return {'wrapper_dir': str(ctx['wrapper_dir'])}

def stage6_post_check(ctx):
    # Check if openai_server.py exists
    server_file = ctx['wrapper_dir'] / "openai_server.py"
    if not server_file.exists():
        print_error(f"openai_server.py not found in {ctx['wrapper_dir']}")
        return False
    print_success("Wrapper repository cloned successfully")
    return True

# Stage 7: Choose Installation Mode
def stage7_pre_check(ctx):
    return True

def stage7_action(ctx):
    print_info("Choose installation mode for the Perplexity wrapper:")
    print("1. Developer mode (-e): Recommended for development. Changes to the source code will be reflected immediately.")
    print("2. Regular mode: Standard installation.")
    
    choice = input("Enter your choice (1 or 2) [1]: ").strip()
    
    if choice == '2':
        ctx['install_mode'] = 'regular'
        print_info("Selected regular installation mode.")
    else:
        ctx['install_mode'] = 'developer'
        print_info("Selected developer installation mode.")
        
    return {'install_mode': ctx['install_mode']}

def stage7_post_check(ctx):
    return 'install_mode' in ctx

# Stage 8: Install Wrapper Dependencies (UPDATED)
def stage8_pre_check(ctx):
    return ctx['venv_pip'].exists() and ctx['wrapper_dir'].exists()

def stage8_action(ctx):
    print_info("Installing wrapper dependencies in venv...")

    install_command = f'"{ctx["venv_pip"]}" install'
    if ctx.get('install_mode') == 'developer':
        install_command += ' -e'

    # Check for requirements.txt
    req_file = ctx['wrapper_dir'] / "requirements.txt"
    if req_file.exists():
        print_info(f"Installing from requirements.txt in {ctx['install_mode']} mode...")
        run_command(f'{install_command} -r "{req_file}"')
    else:
        print_info(f"Installing base dependencies in {ctx['install_mode']} mode...")
        run_command(f'{install_command} .')

    return None

def stage8_post_check(ctx):
    try:
        result = run_command(f'"{ctx["venv_pip"]}" list', capture_output=True)
        required = ['fastapi', 'uvicorn']
        for pkg in required:
            if pkg not in result.lower():
                print_error(f"Package {pkg} not found in venv")
                return False
        print_success("All wrapper dependencies installed in venv")
        return True
    except:
        return False

# Stage 9: Install LiteLLM (in venv)
def stage9_pre_check(ctx):
    return ctx['venv_pip'].exists()

def stage9_action(ctx):
    print_info("Installing LiteLLM in venv...")
    run_command(f'"{ctx["venv_pip"]}" install "litellm[proxy]" pyyaml')
    return None

def stage9_post_check(ctx):
    try:
        result = run_command(f'"{ctx["venv_pip"]}" list', capture_output=True)
        if 'litellm' in result.lower() and 'pyyaml' in result.lower():
            print_success("LiteLLM installed in venv")
            return True
        return False
    except:
        return False

# Stage 10: Create LiteLLM Config
def stage10_pre_check(ctx):
    return ctx['install_dir'].exists()

def stage10_action(ctx):
    print_info("Creating LiteLLM configuration...")

    config_content = """model_list:
  - model_name: claude-sonnet-4.5
    litellm_params:
      model: openai/perplexity-auto
      api_base: http://localhost:8000/v1
      api_key: dummy

  - model_name: claude-opus-4.5
    litellm_params:
      model: openai/perplexity-research
      api_base: http://localhost:8000/v1
      api_key: dummy

  - model_name: claude-haiku-4
    litellm_params:
      model: openai/perplexity-sonar
      api_base: http://localhost:8000/v1
      api_key: dummy

litellm_settings:
  set_verbose: false
  drop_params: true
"""

    config_file = ctx['install_dir'] / "litellm_config.yaml"
    with open(config_file, 'w') as f:
        f.write(config_content)

    ctx['litellm_config'] = config_file
    print_info(f"Config created: {config_file}")
    return {'config_file': str(config_file)}

def stage10_post_check(ctx):
    config_file = ctx['install_dir'] / "litellm_config.yaml"
    return config_file.exists() and config_file.stat().st_size > 0

# Stage 11: Get Session Token (UPDATED - saved in wrapper dir)
def stage11_pre_check(ctx):
    # Check if token already exists in wrapper dir
    token_file = ctx['wrapper_dir'] / ".env"
    if token_file.exists():
        print_info(".env file already exists in wrapper directory")
        use_existing = input("Use existing token? (Y/n): ").strip().lower()
        if use_existing != 'n':
            with open(token_file) as f:
                for line in f:
                    if line.startswith('PERPLEXITY_SESSION_TOKEN='):
                        ctx['session_token'] = line.split('=', 1)[1].strip()
                        break
            return False  # Skip this stage
    return True

def stage11_action(ctx):
    print()
    print_header("Perplexity Session Token Setup")
    print()
    print("You need a Perplexity Pro/Max account session token.")
    print()
    print("Options:")
    print("1. Enter token manually (from browser)")
    print("2. Skip for now (configure later)")
    print()

    choice = input("Choose option (1 or 2): ").strip()

    if choice == "2":
        print_warning("Skipping token setup - configure later in .env file")
        ctx['session_token'] = "CONFIGURE_ME"
    else:
        print()
        print("To get your token:")
        print("1. Go to perplexity.ai and log in")
        print("2. Open DevTools (F12)")
        print("3. Go to Application → Cookies → perplexity.ai")
        print("4. Copy '__Secure-next-auth.session-token' value")
        print()
        token = input("Enter session token (or press Enter to skip): ").strip()

        if not token:
            print_warning("No token provided - configure later")
            ctx['session_token'] = "CONFIGURE_ME"
        else:
            ctx['session_token'] = token

    # Save to wrapper directory .env (where openai_server.py expects it)
    env_file = ctx['wrapper_dir'] / ".env"
    with open(env_file, 'w') as f:
        f.write(f"PERPLEXITY_SESSION_TOKEN={ctx['session_token']}\n")

    # Also save backup in install dir
    backup_token_file = ctx['install_dir'] / ".perplexity_token"
    with open(backup_token_file, 'w') as f:
        f.write(ctx['session_token'])

    print_success(f"Token saved to {env_file}")

    return {'env_file': str(env_file), 'backup': str(backup_token_file)}

def stage11_post_check(ctx):
    env_file = ctx['wrapper_dir'] / ".env"
    return env_file.exists()

# Stage 12: Create Info File
def stage12_pre_check(ctx):
    return True

def stage12_action(ctx):
    print_info("Creating installation info file...")

    info_content = f"""Claude Code + Perplexity Integration
{'=' * 60}

Installation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Python Version: {ctx.get('python_version', 'unknown')}
Repository: https://github.com/urdead12/perplexity-openai-api-updated

Installation Directory: {ctx['install_dir']}
Virtual Environment: {ctx['venv_dir']}
Wrapper Directory: {ctx['wrapper_dir']}
Configuration: {ctx.get('litellm_config', 'N/A')}

Session Token: {ctx['wrapper_dir'] / '.env'}
Backup Token: {ctx['install_dir'] / '.perplexity_token'}

To launch:
  python {ctx['install_dir'].parent / 'launch_claude_perplexity.py'}

Or manually:
  1. cd {ctx['wrapper_dir']}
  2. {ctx['venv_python']} openai_server.py

Services:
  - Perplexity Wrapper: http://localhost:8000
  - LiteLLM Proxy: http://localhost:8080

Configuration:
  Edit {ctx['install_dir']}/litellm_config.yaml to change model mappings
  Edit {ctx['wrapper_dir']}/.env to update session token

Troubleshooting:
  - Wrapper must run from {ctx['wrapper_dir']} (where .env is)
  - Use venv Python: {ctx['venv_python']}
  - Check logs in wrapper directory
  - Verify session token is valid
  - Ensure ports 8000 and 8080 are available
"""

    info_file = ctx['install_dir'] / "INSTALLATION_INFO.txt"
    with open(info_file, 'w') as f:
        f.write(info_content)

    return {'info_file': str(info_file)}

def stage12_post_check(ctx):
    info_file = ctx['install_dir'] / "INSTALLATION_INFO.txt"
    return info_file.exists()

def create_stages() -> List[InstallationStage]:
    """Create all installation stages"""
    return [
        InstallationStage(
            "python_check",
            "Check Python version",
            stage1_pre_check,
            stage1_action,
            stage1_post_check,
            required=True
        ),
        InstallationStage(
            "git_check",
            "Check for Git",
            stage2_pre_check,
            stage2_action,
            stage2_post_check,
            required=True  # Git is required for this version
        ),
        InstallationStage(
            "install_dir_setup",
            "Create installation directory",
            stage3_pre_check,
            stage3_action,
            stage3_post_check,
            rollback=stage3_rollback,
            required=True
        ),
        InstallationStage(
            "venv_setup",
            "Create virtual environment",
            stage4_pre_check,
            stage4_action,
            stage4_post_check,
            rollback=stage4_rollback,
            required=True
        ),
        InstallationStage(
            "pip_upgrade",
            "Upgrade pip in venv",
            stage5_pre_check,
            stage5_action,
            stage5_post_check,
            required=True
        ),
        InstallationStage(
            "clone_wrapper",
            "Clone Perplexity wrapper repository",
            stage6_pre_check,
            stage6_action,
            stage6_post_check,
            required=True
        ),
        InstallationStage(
            "choose_install_mode",
            "Choose installation mode",
            stage7_pre_check,
            stage7_action,
            stage7_post_check,
            required=True
        ),
        InstallationStage(
            "install_wrapper_deps",
            "Install wrapper dependencies in venv",
            stage8_pre_check,
            stage8_action,
            stage8_post_check,
            required=True
        ),
        InstallationStage(
            "install_litellm",
            "Install LiteLLM in venv",
            stage9_pre_check,
            stage9_action,
            stage9_post_check,
            required=True
        ),
        InstallationStage(
            "create_config",
            "Create LiteLLM configuration",
            stage10_pre_check,
            stage10_action,
            stage10_post_check,
            required=True
        ),
        InstallationStage(
            "session_token",
            "Configure session token",
            stage11_pre_check,
            stage11_action,
            stage11_post_check,
            required=False
        ),
        InstallationStage(
            "create_info",
            "Create installation info",
            stage12_pre_check,
            stage12_action,
            stage12_post_check,
            required=True
        ),
    ]

def show_installation_progress(state: InstallationState, total_stages: int):
    """Show current installation progress"""
    completed = len(state.state['completed_stages'])
    print()
    print_info(f"Installation Progress: {completed}/{total_stages} stages completed")
    if state.state['completed_stages']:
        print_info("Completed stages:")
        for stage in state.state['completed_stages']:
            print(f"  ✓ {stage}")
    print()

def main():
    """Main installation routine"""
    print_header("Claude Code + Perplexity Smart Installer")
    print_info("Repository: github.com/urdead12/perplexity-openai-api-updated")

    # Setup state tracking
    state_file = Path.home() / ".claude-perplexity" / ".install_state.json"
    state_file.parent.mkdir(exist_ok=True)
    state = InstallationState(state_file)

    # Create context
    context = {'state': state}

    # Create installation stages
    stages = create_stages()

    # Check if we're resuming
    if state.state['completed_stages']:
        print_info("Detected previous installation attempt")
        show_installation_progress(state, len(stages))

        print()
        print("Options:")
        print("1. Continue from where we left off")
        print("2. Start fresh (reset progress)")
        print("3. Exit")
        print()

        choice = input("Choose option (1-3): ").strip()

        if choice == "2":
            print_warning("Resetting installation state...")
            state.reset()
        elif choice == "3":
            print_info("Exiting")
            return

    try:
        # Execute stages
        for i, stage in enumerate(stages, 1):
            print()
            print_header(f"Stage {i}/{len(stages)}: {stage.description}")

            # Skip if already completed
            if state.is_stage_complete(stage.name):
                print_success(f"Already completed, skipping...")
                continue

            # Execute stage
            stage.execute(context)

        # Installation complete
        print()
        print_header("Installation Complete!")
        print()
        print_success("All stages completed successfully!")
        print()
        print_info("Installation directory:")
        print(f"  {context['install_dir']}")
        print()
        print_info("Wrapper directory:")
        print(f"  {context['wrapper_dir']}")
        print()
        print_info("Next steps:")
        print(f"  1. Review: {context['install_dir'] / 'INSTALLATION_INFO.txt'}")
        print(f"  2. Launch: python launch_claude_perplexity.py")
        print()

        if context.get('session_token') == "CONFIGURE_ME":
            print_warning("Remember to configure your session token in:")
            print(f"  {context['wrapper_dir'] / '.env'}")
            print()

        # Clean up state file
        state_file.unlink()

    except KeyboardInterrupt:
        print()
        print_warning("Installation interrupted by user")
        print_info("Progress has been saved. Run again to continue.")
        sys.exit(1)

    except Exception as e:
        print()
        print_error(f"Installation failed: {e}")
        print()
        print_info("Progress has been saved. You can:")
        print("1. Fix the issue and run installer again to continue")
        print("2. Check the error above for troubleshooting")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
