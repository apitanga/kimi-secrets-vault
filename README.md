# 🔐 Nakimi

Secure, plugin-based API credential management for AI assistants.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/docs-GitHub_Pages-blue)](https://apitanga.github.io/nakimi/)

A personal vault that stores API credentials encrypted at rest, decrypts them just-in-time during sessions, and cleans up automatically when done. Designed for individual developers using AI assistants locally — not an enterprise secrets manager.

## Quick Start

**1. Install age** (required system dependency):

```bash
brew install age          # macOS
sudo apt install age      # Ubuntu/Debian
sudo dnf install age      # Fedora
```

**2. Install nakimi:**

```bash
pip install git+https://github.com/apitanga/nakimi.git
```

**3. Initialize your vault:**

```bash
nakimi init
# Creates ~/.nakimi/key.txt (private) and key.txt.pub
# Back up your private key offline — losing it = losing access to all secrets
```

**4. Add credentials and use:**

```bash
# Set up Gmail (see the full guide in the docs)
# Then:
nakimi gmail.unread
nakimi gmail.search "from:boss"
nakimi session   # interactive session, same commands work inside
```

See the [Installation Guide](https://apitanga.github.io/nakimi/getting-started/) and [Gmail Setup](https://apitanga.github.io/nakimi/plugins/GMAIL_SETUP/) for the full walkthrough.

## Plugins

| Plugin | Status | Description |
|--------|--------|-------------|
| **gmail** | ✅ Ready | Read, search, and send emails |
| **calendar** | 🚧 Planned | Google Calendar integration |
| **github** | 🚧 Planned | GitHub API integration |

Plugins auto-load when you add credentials for them. Adding a new service is just a directory and a class — see the [Plugin Development Guide](https://apitanga.github.io/nakimi/development/PLUGIN_DEVELOPMENT/).

## Security

- Encryption via [age](https://age-encryption.org) — modern, auditable, simple
- Optional [YubiKey](https://www.yubico.com) PIV support for hardware-backed keys
- Decrypted secrets go to `/dev/shm` (RAM) when available, fall back to `/tmp` with `chmod 600` + `shred` cleanup
- Each session gets its own temp file; cleaned up on exit

Full threat model and details: [Security Documentation](https://apitanga.github.io/nakimi/security/).

## Roadmap

- [x] Plugin architecture
- [x] Gmail plugin
- [ ] Google Calendar plugin
- [ ] GitHub plugin
- [ ] Custom HTTP API plugin
- [ ] MCP server mode

## Contributing

Contributions welcome. The plugin architecture makes it straightforward to add new services. See the [Development docs](https://apitanga.github.io/nakimi/development/) for architecture, testing, and plugin guides.

## License

MIT — see [LICENSE](LICENSE).
