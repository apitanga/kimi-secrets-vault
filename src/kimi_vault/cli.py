"""
Command-line interface for Kimi Secrets Vault

Provides CLI access to vault operations without needing to write Python code.
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Kimi Secrets Vault - CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s unread                    # List unread emails
  %(prog)s search "from:boss"        # Search emails
  %(prog)s labels                    # List Gmail labels
  %(prog)s profile                   # Show Gmail profile
  %(prog)s draft to@example.com "Subject" "Body"
        """
    )
    
    parser.add_argument(
        "--secrets",
        "-s",
        help="Path to secrets JSON file (default: auto-detect)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # unread command
    unread_parser = subparsers.add_parser("unread", help="List unread emails")
    unread_parser.add_argument("--limit", "-n", type=int, default=10, help="Maximum emails to show")
    
    # search command
    search_parser = subparsers.add_parser("search", help="Search emails")
    search_parser.add_argument("query", help="Search query (Gmail search syntax)")
    search_parser.add_argument("--limit", "-n", type=int, default=10, help="Maximum emails to show")
    
    # labels command
    subparsers.add_parser("labels", help="List Gmail labels")
    
    # profile command
    subparsers.add_parser("profile", help="Show Gmail profile")
    
    # draft command
    draft_parser = subparsers.add_parser("draft", help="Create email draft")
    draft_parser.add_argument("to", help="Recipient email")
    draft_parser.add_argument("subject", help="Email subject")
    draft_parser.add_argument("body", help="Email body")
    
    # send command
    send_parser = subparsers.add_parser("send", help="Send email immediately")
    send_parser.add_argument("to", help="Recipient email")
    send_parser.add_argument("subject", help="Email subject")
    send_parser.add_argument("body", help="Email body")
    send_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    
    # Init command
    subparsers.add_parser("init", help="Initialize vault directory and generate key")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Handle init command (doesn't need Gmail client)
    if args.command == "init":
        from .crypto import VaultCrypto
        from .config import VaultConfig
        
        config = VaultConfig()
        config.ensure_directories()
        
        crypto = VaultCrypto()
        
        if crypto.key_file.exists():
            print(f"✅ Key already exists: {crypto.key_file}")
            print(f"   Public key: {crypto.get_public_key()}")
        else:
            print("🔐 Generating new age key pair...")
            public_key = crypto.generate_key()
            print(f"✅ Key generated!")
            print(f"   Private key: {crypto.key_file}")
            print(f"   Public key: {public_key}")
            print()
            print("⚠️  IMPORTANT: Back up your private key to a secure location!")
            print("   If you lose this key, you cannot decrypt your secrets.")
        
        print()
        print(f"Vault directory: {config.vault_dir}")
        print(f"Config directory: {config.config_dir}")
        return
    
    # Import client for other commands
    from .client import GmailClient, GmailAuthError
    
    # Get secrets file
    secrets_file = args.secrets
    if not secrets_file:
        secrets_file = sys.environ.get("KIMI_VAULT_SECRETS") or sys.environ.get("KIMI_BOT_SECRETS")
    
    try:
        client = GmailClient(secrets_file)
    except GmailAuthError as e:
        print(f"\n❌ Gmail authentication failed: {e}")
        print("\nTo fix this:")
        print("1. Make sure you're running within 'kimi-vault-session'")
        print("2. Or provide --secrets /path/to/secrets.json")
        print("3. Check your credentials in the secrets file")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Failed to initialize Gmail client: {e}")
        sys.exit(1)
    
    # Execute command
    if args.command == "unread":
        emails = client.list_unread(max_results=args.limit)
        if emails is None:
            print("\n⚠️  Could not fetch emails due to authentication error.")
            sys.exit(1)
        elif emails:
            print(f"\n📧 {len(emails)} Unread Email(s):\n")
            for i, email in enumerate(emails, 1):
                print(f"{i}. {email['subject']}")
                print(f"   From: {email['from']}")
                print(f"   Date: {email['date']}")
                if email['snippet']:
                    print(f"   {email['snippet']}...")
                print()
        else:
            print("\n📭 No unread emails")
    
    elif args.command == "labels":
        labels = client.list_labels()
        if labels is None:
            print("\n⚠️  Could not fetch labels due to authentication error.")
            sys.exit(1)
        else:
            print(f"\n🏷️  {len(labels)} Label(s):\n")
            for label in labels:
                print(f"  - {label['name']}")
    
    elif args.command == "profile":
        profile = client.get_profile()
        if profile is None:
            print("\n⚠️  Could not fetch profile due to authentication error.")
            sys.exit(1)
        else:
            print(f"\n👤 Gmail Profile:")
            print(f"  Email: {profile.get('emailAddress', 'N/A')}")
            print(f"  Messages: {profile.get('messagesTotal', 'N/A')}")
            print(f"  Threads: {profile.get('threadsTotal', 'N/A')}")
    
    elif args.command == "search":
        emails = client.search_emails(args.query, max_results=args.limit)
        if emails is None:
            print(f"\n⚠️  Could not search due to authentication error.")
            sys.exit(1)
        elif emails:
            print(f"\n🔍 {len(emails)} Result(s) for '{args.query}':\n")
            for i, email in enumerate(emails, 1):
                print(f"{i}. {email['subject']}")
                print(f"   From: {email['from']}")
                print(f"   Date: {email['date']}")
                if email['snippet']:
                    print(f"   {email['snippet']}...")
                print()
        else:
            print(f"\n📭 No emails found for '{args.query}'")
    
    elif args.command == "draft":
        draft = client.create_draft(args.to, args.subject, args.body)
        if draft:
            print(f"\n📄 Draft created with ID: {draft['id']}")
        else:
            print("\n⚠️  Could not create draft.")
            sys.exit(1)
    
    elif args.command == "send":
        if not args.yes:
            confirm = input(f"\nSend email to {args.to}? (yes/no): ")
            if confirm.lower() not in ('yes', 'y'):
                print("❌ Cancelled")
                return
        
        sent = client.send_email(args.to, args.subject, args.body)
        if sent:
            print(f"\n✉️  Email sent! Message ID: {sent['id']}")
        else:
            print("\n⚠️  Could not send email.")
            sys.exit(1)


if __name__ == "__main__":
    main()
