#!/usr/bin/env python3
"""
OpenCode + Perplexity Launcher
Starts Perplexity OpenAI server and launches OpenCode
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from setup.common.utils import (
    Colors,
    print_header,
    print_success,
    print_info,
    print_warning,
    print_error,
)
from setup.common.launcher_utils import (
    is_port_in_use,
    check_service_health,
    start_perplexity_server,
    stop_process,
    fetch_available_models,
    get_install_dir,
    LogManager,
    ServiceMonitor,
)


def check_opencode_installed() -> bool:
    """Check if OpenCode is installed"""
    try:
        subprocess.run(
            "opencode --version",
            shell=True,
            capture_output=True,
            check=True
        )
        return True
    except:
        return False


def update_opencode_models(models: list):
    """Update OpenCode configuration with discovered models"""
    import json

    config_file = Path.home() / ".config" / "opencode" / "opencode.json"

    if not config_file.exists():
        print_warning(f"OpenCode config not found at {config_file}")
        return

    try:
        # Read existing config
        with open(config_file, 'r') as f:
            config = json.load(f)

        # Update models in perplexity provider
        if 'provider' not in config:
            config['provider'] = {}

        if 'perplexity' not in config['provider']:
            config['provider']['perplexity'] = {
                "npm": "@ai-sdk/openai-compatible",
                "name": "Perplexity AI",
                "options": {
                    "baseURL": "http://localhost:8000/v1",
                    "apiKey": "dummy"
                },
                "models": {}
            }

        # Add discovered models
        for model in models:
            model_id = model.replace("perplexity-", "")
            if model_id not in config['provider']['perplexity']['models']:
                config['provider']['perplexity']['models'][model_id] = {
                    "name": model.replace("-", " ").title()
                }

        # Write updated config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

        print_success(f"Updated OpenCode with {len(models)} models")

    except Exception as e:
        print_warning(f"Failed to update OpenCode config: {e}")


def launch_opencode(extra_args: list = None):
    """Launch OpenCode"""
    print()
    print_header("Launching OpenCode with Perplexity Backend")
    print()

    # Check if OpenCode is installed
    if not check_opencode_installed():
        print_error("OpenCode is not installed")
        print()
        print_info("Install OpenCode using one of:")
        print("  • curl -fsSL https://opencode.ai/install | bash")
        print("  • npm i -g opencode-ai@latest")
        print("  • brew install opencode")
        print()
        return

    print_info("OpenCode is installed")
    print()
    print_info("Configuration:")
    print(f"  Server URL: http://localhost:8000/v1")
    print(f"  Default Model: perplexity/perplexity-auto")
    print()

    try:
        # Build command
        cmd = ["opencode"]
        if extra_args:
            cmd.extend(extra_args)
            print_info(f"Extra arguments: {' '.join(extra_args)}")
            print()

        print_info("Starting OpenCode...")
        print()

        # Run OpenCode
        subprocess.run(cmd)

    except KeyboardInterrupt:
        print()
        print_warning("OpenCode session ended")
    except Exception as e:
        print()
        print_error(f"Failed to launch OpenCode: {e}")


def main():
    """Main launcher routine"""
    import argparse

    parser = argparse.ArgumentParser(
        description="OpenCode + Perplexity Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch_opencode_perplexity.py
    Start server and launch OpenCode

  python launch_opencode_perplexity.py --server-only
    Start server only (keep it running)

  python launch_opencode_perplexity.py --opencode-only
    Launch OpenCode with existing server

  python launch_opencode_perplexity.py -- /path/to/project
    Launch OpenCode with a specific project directory
        """
    )
    parser.add_argument(
        "--server-only",
        action="store_true",
        help="Start server only and keep it running"
    )
    parser.add_argument(
        "--opencode-only",
        action="store_true",
        help="Launch OpenCode with existing server (don't start server)"
    )

    # Parse known args and capture unknown args to pass to OpenCode
    args, extra_args = parser.parse_known_args()

    # Remove '--' separator if present
    if extra_args and extra_args[0] == '--':
        extra_args = extra_args[1:]

    server_process = None
    log_manager = None
    monitor = None

    try:
        # Get installation directory
        install_dir = get_install_dir("opencode")
        repo_dir = install_dir / "perplexity-openai-api-updated"
        venv_python = install_dir / "venv" / ("Scripts/python.exe" if os.name == 'nt' else "bin/python")

        print_header("OpenCode + Perplexity Launcher")
        print_info(f"Installation directory: {install_dir}")
        print_info(f"Repository: {repo_dir}")
        print()

        if args.opencode_only:
            # Only launch OpenCode (server should already be running)
            print_info("OpenCode-only mode - checking if server is running...")
            if not is_port_in_use(8000):
                print_error("Server is not running on port 8000")
                print_info("Please start the server first or run without --opencode-only")
                sys.exit(1)

            if not check_service_health("http://localhost:8000/health"):
                print_warning("Server port is in use but not responding")
                response = input("Continue anyway? (y/N): ").strip().lower()
                if response != 'y':
                    sys.exit(1)

            launch_opencode(extra_args)

        else:
            # Create log manager
            log_manager = LogManager(install_dir)

            # Start server (unless already running)
            if is_port_in_use(8000):
                if check_service_health("http://localhost:8000/health"):
                    print_success("Perplexity server is already running on port 8000")
                else:
                    print_error("Port 8000 is in use but server is not responding")
                    print_info("Please stop the process using port 8000 and try again")
                    sys.exit(1)
            else:
                # Start the server with log manager
                server_process = start_perplexity_server(repo_dir, venv_python, log_manager)

            # Start service monitor
            if server_process:
                monitor = ServiceMonitor({
                    "Perplexity Server": (server_process, "http://localhost:8000/health")
                })
                monitor.start()

            # Fetch and update models
            print()
            print_info("Discovering available models...")
            models = fetch_available_models()

            if models:
                print_success(f"Found {len(models)} models")
                for model in models[:5]:
                    print(f"  • {model}")
                if len(models) > 5:
                    print(f"  ... and {len(models) - 5} more")

                # Update OpenCode config with discovered models
                update_opencode_models(models)
            else:
                print_warning("No models discovered (using defaults)")

            print()

            if args.server_only:
                # Keep server running
                print_success("Server is running!")
                print_info("Perplexity Server: http://localhost:8000")
                print()
                print_info(f"Logs directory: {log_manager.logs_dir}")
                print()

                # Open tail windows on Windows
                if server_process and log_manager:
                    log_manager.open_tail_windows(["Perplexity"])

                print_info("Press Ctrl+C to stop the server...")
                print()

                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print()
                    print_info("Shutting down...")
            else:
                # Open tail windows on Windows
                if server_process and log_manager:
                    log_manager.open_tail_windows(["Perplexity"])

                # Launch OpenCode
                launch_opencode(extra_args)

    except KeyboardInterrupt:
        print()
        print_warning("Interrupted by user")
    except FileNotFoundError as e:
        print()
        print_error(str(e))
        sys.exit(1)
    except Exception as e:
        print()
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Stop monitor
        if monitor:
            monitor.stop()

        # Clean up server process if we started it
        if server_process:
            stop_process(server_process, "Perplexity Server")

        # Close log files
        if log_manager:
            log_manager.close_all()
            print_info(f"Logs saved to: {log_manager.logs_dir}")
            print()


if __name__ == "__main__":
    main()
