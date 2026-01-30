#!/usr/bin/env python3
"""
Perplexity OpenAI API - Unified CLI
Supports both Claude Code and OpenAI variants
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


def print_banner():
    """Print CLI banner"""
    print()
    print(f"{Colors.BOLD}{Colors.OKGREEN}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKGREEN}Perplexity OpenAI API - Unified CLI{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKGREEN}{'=' * 70}{Colors.ENDC}")
    print()


def show_menu():
    """Show main menu"""
    print(f"{Colors.BOLD}Choose a variant:{Colors.ENDC}")
    print()
    print("1. OpenAI Variant")
    print(f"   {Colors.OKCYAN}→ Direct OpenAI API compatibility{Colors.ENDC}")
    print(f"   {Colors.OKCYAN}→ Use with any OpenAI SDK or client{Colors.ENDC}")
    print(f"   {Colors.OKCYAN}→ Simple setup, just start the server{Colors.ENDC}")
    print()
    print("2. Claude Code Variant")
    print(f"   {Colors.OKCYAN}→ Use with Claude Code CLI{Colors.ENDC}")
    print(f"   {Colors.OKCYAN}→ Includes LiteLLM proxy for routing{Colors.ENDC}")
    print(f"   {Colors.OKCYAN}→ Full Claude Code integration{Colors.ENDC}")
    print()
    print("0. Exit")
    print()


def show_action_menu(variant):
    """Show action menu for a variant"""
    print()
    print(f"{Colors.BOLD}What would you like to do?{Colors.ENDC}")
    print()
    print("1. Install dependencies")
    print("2. Launch server")
    print("3. Show usage examples")
    print("0. Back to main menu")
    print()


def install_openai_variant():
    """Install OpenAI variant"""
    print()
    print(f"{Colors.BOLD}Installing OpenAI Variant...{Colors.ENDC}")
    print()

    script_path = Path(__file__).parent / "variants" / "openai" / "installer.py"
    subprocess.run([sys.executable, str(script_path)])


def launch_openai_variant():
    """Launch OpenAI variant"""
    print()
    print(f"{Colors.BOLD}Launching OpenAI Variant...{Colors.ENDC}")
    print()

    # Check for session token
    if not os.getenv("PERPLEXITY_SESSION_TOKEN"):
        print(f"{Colors.WARNING}⚠ PERPLEXITY_SESSION_TOKEN not set{Colors.ENDC}")
        print()
        print("Please set it:")
        print(f"  {Colors.OKCYAN}export PERPLEXITY_SESSION_TOKEN='your_token'{Colors.ENDC}")
        print()
        return

    script_path = Path(__file__).parent / "variants" / "openai" / "launcher.py"
    subprocess.run([sys.executable, str(script_path)])


def show_openai_examples():
    """Show OpenAI variant usage examples"""
    print()
    print(f"{Colors.BOLD}OpenAI Variant - Usage Examples{Colors.ENDC}")
    print()

    print(f"{Colors.OKCYAN}1. Python (using OpenAI SDK):{Colors.ENDC}")
    print("""
    from openai import OpenAI

    client = OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="dummy"
    )

    response = client.chat.completions.create(
        model="perplexity-auto",
        messages=[{"role": "user", "content": "Hello!"}]
    )

    print(response.choices[0].message.content)
""")

    print(f"{Colors.OKCYAN}2. Node.js (using OpenAI SDK):{Colors.ENDC}")
    print("""
    import OpenAI from 'openai';

    const client = new OpenAI({
      baseURL: 'http://localhost:8000/v1',
      apiKey: 'dummy'
    });

    const response = await client.chat.completions.create({
      model: 'perplexity-auto',
      messages: [{ role: 'user', content: 'Hello!' }]
    });

    console.log(response.choices[0].message.content);
""")

    print(f"{Colors.OKCYAN}3. cURL:{Colors.ENDC}")
    print("""
    curl http://localhost:8000/v1/chat/completions \\
      -H "Content-Type: application/json" \\
      -d '{
        "model": "perplexity-auto",
        "messages": [{"role": "user", "content": "Hello!"}]
      }'
""")

    print(f"{Colors.OKCYAN}4. LangChain:{Colors.ENDC}")
    print("""
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(
        base_url="http://localhost:8000/v1",
        api_key="dummy",
        model="perplexity-auto"
    )

    response = llm.invoke("What's the weather like?")
    print(response.content)
""")

    input(f"\n{Colors.OKCYAN}Press Enter to continue...{Colors.ENDC}")


def install_claude_variant():
    """Install Claude variant"""
    print()
    print(f"{Colors.BOLD}Installing Claude Code Variant...{Colors.ENDC}")
    print()

    script_path = Path(__file__).parent / "install_claude_perplexity.py"
    subprocess.run([sys.executable, str(script_path)])


def launch_claude_variant():
    """Launch Claude variant"""
    print()
    print(f"{Colors.BOLD}Launching Claude Code Variant...{Colors.ENDC}")
    print()

    script_path = Path(__file__).parent / "variants" / "claude" / "launcher.py"
    subprocess.run([sys.executable, str(script_path)])


def show_claude_examples():
    """Show Claude variant usage examples"""
    print()
    print(f"{Colors.BOLD}Claude Code Variant - Usage Examples{Colors.ENDC}")
    print()

    print(f"{Colors.OKCYAN}1. Launch Claude Code:{Colors.ENDC}")
    print(f"   {Colors.OKGREEN}python launch_claude_perplexity.py{Colors.ENDC}")
    print()

    print(f"{Colors.OKCYAN}2. Start services only:{Colors.ENDC}")
    print(f"   {Colors.OKGREEN}python launch_claude_perplexity.py --services-only{Colors.ENDC}")
    print()

    print(f"{Colors.OKCYAN}3. Launch Claude with existing services:{Colors.ENDC}")
    print(f"   {Colors.OKGREEN}python launch_claude_perplexity.py --claude-only{Colors.ENDC}")
    print()

    print("The launcher will:")
    print("  - Start Perplexity wrapper (port 8000)")
    print("  - Start LiteLLM proxy (port 8080)")
    print("  - Discover available models")
    print("  - Launch Claude Code with Perplexity backend")
    print()

    input(f"\n{Colors.OKCYAN}Press Enter to continue...{Colors.ENDC}")


def main():
    """Main CLI loop"""
    print_banner()

    while True:
        show_menu()

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
            # OpenAI variant
            while True:
                show_action_menu("OpenAI")

                try:
                    action = input(f"{Colors.OKCYAN}Enter your choice (0-3): {Colors.ENDC}").strip()
                except (KeyboardInterrupt, EOFError):
                    break

                if action == "0":
                    break
                elif action == "1":
                    install_openai_variant()
                elif action == "2":
                    launch_openai_variant()
                elif action == "3":
                    show_openai_examples()
                else:
                    print(f"{Colors.WARNING}Invalid choice{Colors.ENDC}")

        elif choice == "2":
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
                    install_claude_variant()
                elif action == "2":
                    launch_claude_variant()
                elif action == "3":
                    show_claude_examples()
                else:
                    print(f"{Colors.WARNING}Invalid choice{Colors.ENDC}")

        else:
            print(f"{Colors.WARNING}Invalid choice{Colors.ENDC}")


if __name__ == "__main__":
    main()
