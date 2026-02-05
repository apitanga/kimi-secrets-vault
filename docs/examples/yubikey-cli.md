# YubiKey CLI Examples

## Basic Setup

```bash
# Check if ykman is installed
ykman --version

# Enable YubiKey in Nakimi
export NAKIMI_YUBIKEY_ENABLED=true

# Configure PIV slot (default: 1)
export NAKIMI_YUBIKEY_SLOT=1

# Initialize YubiKey for use with Nakimi
nakimi yubikey setup --slot 1

# Encrypt existing age key with YubiKey
nakimi yubikey encrypt-key
```

## Daily Usage

```bash
# Check YubiKey status
nakimi yubikey status

# Start a secure session (automatically uses YubiKey if enabled)
nakimi session

# Verify PIN (for testing)
nakimi yubikey verify-pin 123456

# Change PIN
nakimi yubikey change-pin 123456 654321
```

## Testing and Debugging

```bash
# Test decryption of age key
nakimi yubikey decrypt-key

# Check ykman directly
ykman info
ykman piv info
ykman piv info slot 1
```

## Environment Variables

```bash
# Enable YubiKey
export NAKIMI_YUBIKEY_ENABLED=true

# Set PIV slot (1 is used by default)
export NAKIMI_YUBIKEY_SLOT=1

# Require touch confirmation (default: true)
export NAKIMI_YUBIKEY_REQUIRE_TOUCH=true

# Enable PIN prompt (default: true)
export NAKIMI_YUBIKEY_PIN_PROMPT=true

# Disable touch requirement
export NAKIMI_YUBIKEY_REQUIRE_TOUCH=false

# Disable PIN prompt (not recommended)
export NAKIMI_YUBIKEY_PIN_PROMPT=false
```

## Troubleshooting

### YubiKey Not Detected

```bash
# Check if ykman is installed
which ykman

# Check if YubiKey is connected
ykman info

# Check USB permissions (Linux)
lsusb | grep -i yubikey
sudo dmesg | grep -i yubikey
```

### PIN Issues

```bash
# Verify PIN works
ykman piv verify-pin 123456

# Reset PIV application (WARNING: erases all PIV data)
ykman piv reset
```

### Encryption/Decryption Errors

```bash
# Check if age key exists in Nakimi
ls -la ~/.nakimi/key.txt

# Test age encryption/decryption without YubiKey
age -r $(cat ~/.nakimi/key.txt.pub) -o test.age test.txt
age -d -i ~/.nakimi/key.txt test.age
```