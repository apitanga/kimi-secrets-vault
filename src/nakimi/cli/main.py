"""
Main CLI entry point for Nakimi

Provides plugin-based command execution and vault management.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from nakimi.core import Vault, VaultConfig, get_config, secure_delete
from nakimi.core.plugin import PluginManager, PluginError

# Version - sync with pyproject.toml
__version__ = "2.0.0"


def get_secrets_path() -> Path:
    """Get secrets file path from env or config"""
    # Priority: NAKIMI_SECRETS > NAKIMI_BOT_SECRETS > config default
    env_path = os.environ.get("NAKIMI_SECRETS") or os.environ.get("NAKIMI_BOT_SECRETS")
    if env_path:
        return Path(env_path)
    
    config = get_config()
    return config.secrets_file


def load_secrets() -> dict:
    """Load and parse secrets JSON"""
    secrets_path = get_secrets_path()
    
    if not secrets_path.exists():
        raise PluginError(
            f"No secrets file found at {secrets_path}\n"
            "Run 'nakimi init' to set up your vault."
        )
    
    # Check if file is encrypted (.age extension)
    if str(secrets_path).endswith('.age'):
        # Need to decrypt first
        vault = Vault()
        temp_path = vault.decrypt(secrets_path)
        try:
            with open(temp_path, 'r') as f:
                return json.load(f)
        finally:
            secure_delete(temp_path)
    else:
        # Plaintext JSON
        with open(secrets_path, 'r') as f:
            return json.load(f)


def cmd_init(args):
    """Initialize vault and generate keys"""
    config = get_config()
    config.ensure_directories()
    
    vault = Vault()
    
    if vault.key_file.exists():
        print(f"✅ Key already exists: {vault.key_file}")
        print(f"   Public key: {vault.get_public_key()}")
    else:
        print("🔐 Generating new age key pair...")
        public_key = vault.generate_key()
        print(f"✅ Key generated!")
        print(f"   Private key: {vault.key_file}")
        print(f"   Public key: {public_key}")
        print()
        print("⚠️  IMPORTANT: Back up your private key to a secure location!")
        print("   If you lose this key, you CANNOT decrypt your secrets.")


def cmd_encrypt(args):
    """Encrypt a file"""
    vault = Vault()
    
    input_file = Path(args.file)
    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        sys.exit(1)
    
    output_file = args.output or f"{input_file}.age"
    
    print(f"🔐 Encrypting {input_file}...")
    result = vault.encrypt(input_file, output_file)
    print(f"✅ Encrypted to: {result}")
    
    if args.shred:
        print(f"🧹 Securely deleting original...")
        secure_delete(input_file)


def cmd_decrypt(args):
    """Decrypt a file"""
    vault = Vault()
    
    input_file = Path(args.file)
    if not input_file.exists():
        print(f"❌ File not found: {input_file}")
        sys.exit(1)
    
    output_file = args.output
    
    print(f"🔓 Decrypting {input_file}...")
    result = vault.decrypt(input_file, output_file)
    print(f"✅ Decrypted to: {result}")
    
    if not args.keep:
        print("⚠️  Warning: Use --keep to preserve decrypted file, or it will be temporary.")


def cmd_plugins(args):
    """List available plugins"""
    try:
        secrets = load_secrets()
    except PluginError as e:
        print(f"⚠️  {e}")
        secrets = {}
    
    manager = PluginManager(secrets)
    
    # Auto-discover plugins
    manager.discover_plugins()
    
    if args.command == "list":
        plugins = manager.list_plugins()
        if plugins:
            print("Loaded plugins:")
            for name in plugins:
                plugin = manager.get_plugin(name)
                print(f"  • {name:15} - {plugin.description}")
        else:
            print("No plugins loaded.")
            print("Add credentials to your secrets.json to enable plugins.")
    
    elif args.command == "commands":
        commands = manager.list_commands()
        if commands:
            print("Available commands:")
            for cmd in sorted(commands):
                print(f"  {cmd}")
        else:
            print("No commands available.")


def cmd_run(args):
    """Run a plugin command"""
    try:
        secrets = load_secrets()
    except PluginError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    manager = PluginManager(secrets)
    manager.discover_plugins()
    
    full_command = f"{args.plugin}.{args.command}"
    
    try:
        result = manager.execute_command(full_command, args.args)
        if result:
            print(result)
    except PluginError as e:
        print(f"❌ {e}")
        sys.exit(1)


def cmd_upgrade(args):
    """Upgrade nakimi to latest version from GitHub"""
    repo_url = "https://github.com/apitanga/nakimi.git"
    
    print(f"🔄 Upgrading nakimi...")
    print(f"   Repository: {repo_url}")
    if args.target_version:
        print(f"   Target version: {args.target_version}")
    else:
        print(f"   Target: latest main branch")
    print()
    
    # Construct pip install command
    if args.target_version:
        install_spec = f"git+{repo_url}@{args.target_version}"
    else:
        install_spec = f"git+{repo_url}"
    
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", install_spec]
    
    print(f"Running: pip install --upgrade {install_spec}")
    print()
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        if result.returncode == 0:
            print()
            print("✅ Upgrade complete!")
            print()
            # Show new version
            print("New version:")
            subprocess.run([sys.executable, "-m", "nakimi.cli.main", "--version"])
        else:
            print()
            print(f"❌ Upgrade failed with exit code {result.returncode}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error during upgrade: {e}")
        sys.exit(1)


def cmd_version():
    """Show version information"""
    print(f"nakimi {__version__}")
    print(f"Python {sys.version.split()[0]}")
    print(f"Location: {Path(__file__).parent.parent.parent}")


def cmd_session(args):
    """Start a secure session with decrypted secrets"""
    import subprocess
    import tempfile
    
    config = get_config()
    vault = Vault()
    
    # Check vault exists
    if not config.secrets_file.exists():
        print(f"❌ No encrypted secrets found at {config.secrets_file}")
        print("Run 'nakimi init' to set up your vault.")
        sys.exit(1)
    
    # Decrypt secrets to temp file
    print("🔓 Decrypting vault...")
    try:
        temp_secrets = vault.decrypt(config.secrets_file)
    except Exception as e:
        print(f"❌ Failed to decrypt: {e}")
        sys.exit(1)
    
    print("✅ Vault decrypted")
    print()
    
    # Show available plugins
    try:
        with open(temp_secrets, 'r') as f:
            secrets = json.load(f)
        manager = PluginManager(secrets)
        manager.discover_plugins()
        
        if manager.list_plugins():
            print("Available plugins:")
            for name in manager.list_plugins():
                plugin = manager.get_plugin(name)
                print(f"  ✅ {name} - {plugin.description}")
        else:
            print("⚠️  No plugins configured")
    except Exception:
        pass
    
    print()
    print("💡 Usage: nakimi <plugin>.<command> [args]")
    print("         Example: nakimi gmail.unread")
    print()
    
    # Set up cleanup
    def cleanup():
        if temp_secrets.exists():
            secure_delete(temp_secrets)
            print("\n🔒 Vault closed")
    
    # Export secrets path
    os.environ["NAKIMI_SECRETS"] = str(temp_secrets)
    
    try:
        # Launch shell or kimi
        if args.shell:
            subprocess.run([os.environ.get("SHELL", "/bin/bash")])
        elif args.command:
            # Run specific command
            result = subprocess.run(args.command)
            cleanup()
            sys.exit(result.returncode)
        else:
            # Try to launch kimi, fall back to shell
            try:
                subprocess.run(["kimi"])
            except FileNotFoundError:
                print("kimi not found, starting shell...")
                subprocess.run([os.environ.get("SHELL", "/bin/bash")])
    finally:
        cleanup()


def main():
    # Check for plugin command BEFORE setting up argparse
    # This allows plugin commands like "gmail.unread" to work
    if len(sys.argv) > 1 and "." in sys.argv[1] and not sys.argv[1].startswith("-"):
        plugin_cmd = sys.argv[1]
        if "." in plugin_cmd:
            parts = plugin_cmd.split(".", 1)
            # Create minimal args object for cmd_run
            class Args:
                pass
            args = Args()
            args.plugin = parts[0]
            args.command = parts[1]
            args.args = sys.argv[2:]
            return cmd_run(args)
    
    parser = argparse.ArgumentParser(
        prog="nakimi",
        description="Secure vault for API credentials with plugin-based integrations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s init                          # Initialize vault
  %(prog)s session                       # Start secure session
  %(prog)s gmail.unread                  # List unread emails
  %(prog)s gmail.search "from:boss"      # Search emails
  %(prog)s plugins list                  # List available plugins
  %(prog)s upgrade                       # Upgrade to latest version
        """
    )
    
    # Add version flag
    parser.add_argument("--version", "-v", action="store_true", help="Show version information")
    
    subparsers = parser.add_subparsers(dest="cmd", help="Commands")
    
    # init command
    init_parser = subparsers.add_parser("init", help="Initialize vault and generate keys")
    
    # encrypt command
    encrypt_parser = subparsers.add_parser("encrypt", help="Encrypt a file")
    encrypt_parser.add_argument("file", help="File to encrypt")
    encrypt_parser.add_argument("-o", "--output", help="Output file")
    encrypt_parser.add_argument("--shred", action="store_true", help="Securely delete original after encryption")
    
    # decrypt command
    decrypt_parser = subparsers.add_parser("decrypt", help="Decrypt a file")
    decrypt_parser.add_argument("file", help="File to decrypt")
    decrypt_parser.add_argument("-o", "--output", help="Output file")
    decrypt_parser.add_argument("--keep", action="store_true", help="Keep decrypted file")
    
    # plugins command
    plugins_parser = subparsers.add_parser("plugins", help="Manage plugins")
    plugins_sub = plugins_parser.add_subparsers(dest="command", help="Plugin commands")
    plugins_sub.add_parser("list", help="List available plugins")
    plugins_sub.add_parser("commands", help="List available commands")
    
    # session command
    session_parser = subparsers.add_parser("session", help="Start secure session")
    session_parser.add_argument("--shell", action="store_true", help="Start shell instead of kimi")
    session_parser.add_argument("--exec", dest="command", nargs=argparse.REMAINDER, help="Execute command and exit")
    
    # upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade to latest version from GitHub")
    upgrade_parser.add_argument("--version", dest="target_version", help="Specific version to upgrade to (default: latest)")
    
    # plugin command (direct invocation: nakimi gmail.unread)
    # This is handled specially below
    
    args, remaining = parser.parse_known_args()
    
    # Handle --version flag
    if args.version:
        cmd_version()
        sys.exit(0)
    
    if not args.cmd:
        parser.print_help()
        sys.exit(1)
    
    # Route to appropriate handler
    handlers = {
        "init": cmd_init,
        "encrypt": cmd_encrypt,
        "decrypt": cmd_decrypt,
        "plugins": cmd_plugins,
        "session": cmd_session,
        "upgrade": cmd_upgrade,
    }
    
    handler = handlers.get(args.cmd)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
