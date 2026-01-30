#!/usr/bin/env python3
"""
OpenCode + Perplexity Integration Installer
Installs OpenCode and configures it to use Perplexity OpenAI server
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from setup.common.utils import (
    Colors,
    InstallationState,
    InstallationStage,
    print_header,
    print_success,
    print_info,
    print_warning,
    print_error,
    run_command,
    check_python_version,
    check_git_installed,
    get_perplexity_token,
    create_venv,
    get_venv_python,
    install_pip_package,
    clone_repository,
    create_env_file,
)


def main():
    """Main installation routine"""
    print_header("OpenCode + Perplexity Integration Installer")

    # Installation directory
    install_dir = Path.home() / ".opencode-perplexity"
    state_file = install_dir / "install_state.json"

    print_info(f"Installation directory: {install_dir}")
    print()

    # Initialize state
    state = InstallationState(state_file)
    ctx = {'state': state, 'install_dir': install_dir}

    try:
        # Stage 1: Check Python version
        if not state.is_stage_complete("python_check"):
            print_info("Checking Python version...")
            if not check_python_version(min_major=3, min_minor=10):
                sys.exit(1)
            ctx['python_version'] = f"{sys.version_info.major}.{sys.version_info.minor}"
            ctx['python_path'] = sys.executable
            state.mark_stage_complete("python_check")
            print_success("Python version check passed")

        # Stage 2: Check git (optional)
        if not state.is_stage_complete("git_check"):
            print_info("Checking for git...")
            ctx['has_git'] = check_git_installed()
            if ctx['has_git']:
                print_success("Git is installed")
            else:
                print_warning("Git not found (optional)")
            state.mark_stage_complete("git_check")

        # Stage 3: Create installation directory
        if not state.is_stage_complete("create_dir"):
            print_info("Creating installation directory...")
            install_dir.mkdir(parents=True, exist_ok=True)
            ctx['state'].state['installation_dir'] = str(install_dir)
            state.mark_stage_complete("create_dir")
            print_success(f"Created {install_dir}")

        # Stage 4: Get Perplexity session token
        if not state.is_stage_complete("get_token"):
            print_info("Getting Perplexity session token...")
            token = get_perplexity_token()
            if token:
                ctx['perplexity_token'] = token
                print_success("Session token obtained")
            else:
                print_warning("No token provided - you'll need to set PERPLEXITY_SESSION_TOKEN later")
            state.mark_stage_complete("get_token")

        # Stage 5: Create virtual environment
        if not state.is_stage_complete("create_venv"):
            print_info("Creating virtual environment...")
            venv_path = create_venv(install_dir)
            ctx['venv_path'] = venv_path
            ctx['venv_python'] = get_venv_python(venv_path)
            state.mark_stage_complete("create_venv")
            print_success("Virtual environment created")

        # Make sure venv_python is set for subsequent stages
        if 'venv_python' not in ctx:
            venv_path = install_dir / "venv"
            ctx['venv_path'] = venv_path
            ctx['venv_python'] = get_venv_python(venv_path)

        # Stage 6: Install Python dependencies
        if not state.is_stage_complete("install_deps"):
            print_info("Installing Python dependencies...")
            packages = [
                "fastapi",
                "uvicorn",
                "pydantic",
                "slowapi",
                "curl_cffi",
                "python-dotenv",
                "pyyaml",
            ]
            for package in packages:
                install_pip_package(ctx['venv_python'], package)
            print_success("Python dependencies installed")
            state.mark_stage_complete("install_deps")

        # Stage 7: Clone perplexity-openai-api repository
        repo_dir = install_dir / "perplexity-openai-api-updated"
        if not state.is_stage_complete("clone_repo"):
            if not ctx.get('has_git'):
                print_error("Git is required to clone repository")
                print_info("Please install git and run the installer again")
                sys.exit(1)

            print_info("Cloning perplexity-openai-api-updated repository...")
            if repo_dir.exists():
                print_warning(f"Repository directory already exists at {repo_dir}")
                print_info("Skipping clone")
            else:
                clone_repository(
                    "https://github.com/urdead12/perplexity-openai-api-updated.git",
                    repo_dir
                )
            ctx['repo_dir'] = repo_dir
            print_success("Repository cloned")
            state.mark_stage_complete("clone_repo")

        # Make sure repo_dir is set
        if 'repo_dir' not in ctx:
            ctx['repo_dir'] = repo_dir

        # Stage 8: Install perplexity-webui-scraper
        if not state.is_stage_complete("install_scraper"):
            print_info("Installing perplexity-webui-scraper...")
            run_command(
                f"{ctx['venv_python']} -m pip install -e {ctx['repo_dir']}",
                cwd=str(ctx['repo_dir'])
            )
            print_success("perplexity-webui-scraper installed")
            state.mark_stage_complete("install_scraper")

        # Stage 9: Create .env file
        if not state.is_stage_complete("create_env"):
            print_info("Creating .env file...")
            env_vars = {}
            if ctx.get('perplexity_token'):
                env_vars['PERPLEXITY_SESSION_TOKEN'] = ctx['perplexity_token']
            else:
                env_vars['PERPLEXITY_SESSION_TOKEN'] = 'your_token_here'

            create_env_file(ctx['repo_dir'], env_vars)
            print_success(".env file created")
            state.mark_stage_complete("create_env")

        # Stage 10: Check/Install OpenCode
        if not state.is_stage_complete("check_opencode"):
            print_info("Checking for OpenCode installation...")
            try:
                version = run_command("opencode --version", capture_output=True)
                print_success(f"OpenCode is installed: {version}")
                ctx['opencode_installed'] = True
            except:
                print_warning("OpenCode is not installed")
                print()
                print_info("To install OpenCode, run one of:")
                print("  • curl -fsSL https://opencode.ai/install | bash")
                print("  • npm i -g opencode-ai@latest")
                print("  • brew install opencode")
                print()
                response = input("Would you like to install OpenCode now using npm? (y/N): ").strip().lower()
                if response == 'y':
                    print_info("Installing OpenCode via npm...")
                    run_command("npm i -g opencode-ai@latest")
                    print_success("OpenCode installed")
                    ctx['opencode_installed'] = True
                else:
                    print_warning("Skipping OpenCode installation")
                    print_info("You can install it later and run this installer again")
                    ctx['opencode_installed'] = False

            state.mark_stage_complete("check_opencode")

        # Stage 11: Configure OpenCode
        if not state.is_stage_complete("configure_opencode"):
            if ctx.get('opencode_installed'):
                print_info("Configuring OpenCode to use Perplexity server...")

                # Create OpenCode config directory
                config_dir = Path.home() / ".config" / "opencode"
                config_dir.mkdir(parents=True, exist_ok=True)

                config_file = config_dir / "opencode.json"

                # Create configuration
                config = {
                    "$schema": "https://opencode.ai/config.json",
                    "provider": {
                        "perplexity": {
                            "npm": "@ai-sdk/openai-compatible",
                            "name": "Perplexity AI",
                            "options": {
                                "baseURL": "http://localhost:8000/v1",
                                "apiKey": "dummy"
                            },
                            "models": {
                                "perplexity-auto": {
                                    "name": "Perplexity Auto (Best)"
                                },
                                "perplexity-sonar": {
                                    "name": "Perplexity Sonar (Fast)"
                                },
                                "perplexity-research": {
                                    "name": "Perplexity Research (Deep)"
                                },
                                "perplexity-labs": {
                                    "name": "Perplexity Labs (Experimental)"
                                }
                            }
                        }
                    },
                    "model": "perplexity/perplexity-auto"
                }

                # Write config
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)

                print_success(f"OpenCode configured at {config_file}")
                print_info("Default model set to: perplexity/perplexity-auto")
            else:
                print_warning("Skipping OpenCode configuration (not installed)")

            state.mark_stage_complete("configure_opencode")

        # All done!
        print()
        print_header("Installation Complete!")
        print()
        print_success("OpenCode + Perplexity integration is ready!")
        print()
        print_info("Next steps:")
        print()

        if not ctx.get('perplexity_token'):
            print("1. Get your Perplexity session token:")
            print("   • Log in at https://www.perplexity.ai")
            print("   • Open DevTools (F12) → Application → Cookies")
            print("   • Copy '__Secure-next-auth.session-token' value")
            print()
            print(f"2. Add it to {ctx['repo_dir']}/.env:")
            print("   PERPLEXITY_SESSION_TOKEN=your_token_here")
            print()

        print("3. Start the Perplexity server:")
        print(f"   python {Path(__file__).parent}/launch_opencode_perplexity.py")
        print()

        if ctx.get('opencode_installed'):
            print("4. Use OpenCode with Perplexity:")
            print("   • The server will start automatically")
            print("   • OpenCode will use perplexity/perplexity-auto by default")
            print("   • You can change models in OpenCode settings")
        else:
            print("4. Install OpenCode:")
            print("   curl -fsSL https://opencode.ai/install | bash")
            print()
            print("5. Then run the launcher to use it")

        print()
        print_info(f"Installation directory: {install_dir}")
        print_info(f"Repository: {ctx['repo_dir']}")
        if ctx.get('opencode_installed'):
            print_info(f"OpenCode config: {Path.home() / '.config' / 'opencode' / 'opencode.json'}")
        print()

    except Exception as e:
        print()
        print_error(f"Installation failed: {str(e)}")
        print()
        print_info("You can run the installer again to resume from the last successful stage")
        sys.exit(1)


if __name__ == "__main__":
    main()
