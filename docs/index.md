---
title: HOME
nav_order: 0
---

# Kimi Secrets Vault

Secure, plugin-based API credential management for AI assistants

## Overview
Kimi Secrets Vault is a secure, plugin-based API credential management system for AI assistants with age encryption. It provides encrypted storage for API credentials with just-in-time decryption, plugin-based service integration, and a simple CLI interface.

## Quick Links

- **[Getting Started](./getting-started/INSTALL.md)** - Installation and setup
- **[Gmail Plugin Setup](./plugins/GMAIL_SETUP.md)** - Configure Gmail integration
- **[Plugin Development](./development/PLUGIN_DEVELOPMENT.md)** - Create your own plugins
- **[Architecture](./development/ARCHITECTURE.md)** - System design and security model
- **[Testing Guide](./development/TESTS.md)** - Comprehensive testing documentation
- **[ADR](./development/ADR.md)** - Architecture Decision Records
- **[Security](./security/index.md)** - Security architecture and policies
- **[API Reference](./api/index.md)** - Python API and plugin development

## Core Features

### 🔐 Security First
- Age encryption for credential storage
- RAM-backed temporary files with `mlock()` support
- Secure deletion with `shred`
- Just-in-time decryption

### 🔌 Plugin-Based
- Auto-discovery based on available credentials
- Easy to extend with new services
- Standard plugin interface

### 🖥️ CLI Focused
- Simple `plugin.command` syntax
- Session mode for secure workflows
- Clear error messages with emoji indicators

## Project Status
**Current Version**: 0.1.0 (early development)  
**Test Coverage**: 63% (78 tests passing)  
**Active Development**: Yes

## Getting Help
- [GitHub Issues](https://github.com/apitanga/kimi-secrets-vault/issues) - Report bugs or request features
- [Contributing Guide](../CONTRIBUTING.md) - How to contribute
- [Security Policy](../SECURITY.md) - Security reporting and policies

---

*Documentation last updated: 2026-02-01*