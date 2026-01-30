#!/usr/bin/env python3
"""
Perplexity OpenAI API - Unified Setup CLI
Choose between Claude Code and OpenCode variants
"""

import os
import sys
import subprocess
from pathlib import Path


class Colors:
    """ANSI color codes"""
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    OKCYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    HEADER = '\033[95m'


def print_banner():
    """Print CLI banner"""
    print()
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'Perplexity OpenAI API - Setup CLI'.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print()


def show_main_menu():
    """Show main menu"""
    print(f"{Colors.BOLD}Choose your variant:{Colors.ENDC}")
    print()
    print("1. Claude Code Variant")
    print(f"   {Colors.OKCYAN}→ Use Perplexity with Claude Code CLI{Colors.ENDC}")
    print(f"   {Colors.OKCYAN}→ Includes LiteLLM proxy for model routing{Colors.ENDC}")
    print(f"   {Colors.OKCYAN}→ Full Claude Code integration{Colors.ENDC}")
    print()
    print("2. OpenCode Variant")
    print(f"   {Colors.OKCYAN}→ Use Perplexity with OpenCode CLI (open source){Colors.ENDC}")
    print(f"   {Colors.OKCYAN}→ Direct connection (no proxy needed){Colors.ENDC}")
    print(f"   {Colors.OKCYAN}→ Simpler setup{Colors.ENDC}")
    print()
    print("0. Exit")
    print()


def show_action_menu(variant):
    """Show action menu for a variant"""
    print()
    print(f"{Colors.BOLD}What would you like to do with {variant}?{Colors.ENDC}")
    print()
    print("1. Install")
    print("2. Launch")
    print("3. Show info")
    print("0. Back to main menu")
    print()


def install_claude():
    """Install Claude Code variant"""
    print()
    print(f"{Colors.BOLD}Installing Claude Code Variant...{Colors.ENDC}")
    print()

    script_path = Path(__file__).parent / "install_claude_perplexity.py"
    subprocess.run([sys.executable, str(script_path)])


def launch_claude():
    """Launch Claude Code variant"""
    print()
    print(f"{Colors.BOLD}Launching Claude Code Variant...{Colors.ENDC}")
    print()

    script_path = Path(__file__).parent / "launch_claude_perplexity.py"
    subprocess.run([sys.executable, str(script_path)])


def show_claude_info():
    """Show Claude Code variant information"""
    print()
    print(f"{Colors.BOLD}Claude Code Variant - Information{Colors.ENDC}")
    print()
    print("Architecture:")
    print(f"  {Colors.OKCYAN}Claude Code → LiteLLM Proxy (8080) → Perplexity Server (8000) → Perplexity.ai{Colors.ENDC}")
    print()
    print("What gets installed:")
    print("  • Python virtual environment")
    print("  • Perplexity OpenAI server")
    print("  • LiteLLM proxy")
    print("  • Model discovery and configuration")
    print()
    print("Installation directory:")
    print(f"  {Path.home() / '.claude-perplexity'}")
    print()
    print("Usage:")
    print("  1. Run installer to set up environment")
    print("  2. Get Perplexity session token from cookies")
    print("  3. Run launcher to start services and Claude Code")
    print()
    input(f"{Colors.OKCYAN}Press Enter to continue...{Colors.ENDC}")


def install_opencode():
    """Install OpenCode variant"""
    print()
    print(f"{Colors.BOLD}Installing OpenCode Variant...{Colors.ENDC}")
    print()

    script_path = Path(__file__).parent / "setup" / "opencode" / "install_opencode_perplexity.py"
    subprocess.run([sys.executable, str(script_path)])


def launch_opencode():
    """Launch OpenCode variant"""
    print()
    print(f"{Colors.BOLD}Launching OpenCode Variant...{Colors.ENDC}")
    print()

    script_path = Path(__file__).parent / "setup" / "opencode" / "launch_opencode_perplexity.py"
    subprocess.run([sys.executable, str(script_path)])


def show_opencode_info():
    """Show OpenCode variant information"""
    print()
    print(f"{Colors.BOLD}OpenCode Variant - Information{Colors.ENDC}")
    print()
    print("Architecture:")
    print(f"  {Colors.OKCYAN}OpenCode → Perplexity Server (8000) → Perplexity.ai{Colors.ENDC}")
    print()
    print("What gets installed:")
    print("  • Python virtual environment")
    print("  • Perplexity OpenAI server")
    print("  • OpenCode CLI (optional)")
    print("  • OpenCode configuration")
    print()
    print("Installation directory:")
    print(f"  {Path.home() / '.opencode-perplexity'}")
    print()
    print("OpenCode configuration:")
    print(f"  {Path.home() / '.config' / 'opencode' / 'opencode.json'}")
    print()
    print("Usage:")
    print("  1. Run installer to set up environment")
    print("  2. Get Perplexity session token from cookies")
    print("  3. Run launcher to start server and OpenCode")
    print()
    print("Advantages:")
    print("  • Open source AI coding assistant")
    print("  • No proxy needed (direct connection)")
    print("  • Simpler architecture")
    print()
    input(f"{Colors.OKCYAN}Press Enter to continue...{Colors.ENDC}")


def main():
    """Main CLI loop"""
    print_banner()

    while True:
        show_main_menu()

        try:
            choice = input(f"{Colors.OKCYAN}Enter your choice (0-2): {Colors.ENDC}").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            print(f"{Colors.WARNING}Exiting...{Colors.ENDC}")
            sys.exit(0)

        if choice == "0":
            print()
            print(f"{Colors.OKGREEN}Goodbye!{Colors.ENDC}")
            print()
            sys.exit(0)

        elif choice == "1":
            # Claude Code variant
            while True:
                show_action_menu("Claude Code")

                try:
                    action = input(f"{Colors.OKCYAN}Enter your choice (0-3): {Colors.ENDC}").strip()
                except (KeyboardInterrupt, EOFError):
                    break

                if action == "0":
                    break
                elif action == "1":
                    install_claude()
                elif action == "2":
                    launch_claude()
                elif action == "3":
                    show_claude_info()
                else:
                    print(f"{Colors.WARNING}Invalid choice{Colors.ENDC}")

        elif choice == "2":
            # OpenCode variant
            while True:
                show_action_menu("OpenCode")

                try:
                    action = input(f"{Colors.OKCYAN}Enter your choice (0-3): {Colors.ENDC}").strip()
                except (KeyboardInterrupt, EOFError):
                    break

                if action == "0":
                    break
                elif action == "1":
                    install_opencode()
                elif action == "2":
                    launch_opencode()
                elif action == "3":
                    show_opencode_info()
                else:
                    print(f"{Colors.WARNING}Invalid choice{Colors.ENDC}")

        else:
            print(f"{Colors.WARNING}Invalid choice{Colors.ENDC}")


if __name__ == "__main__":
    main()
