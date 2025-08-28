#!/usr/bin/env python3
"""
Crypto Keys Utility
Provides AES encryption for API keys at rest with secure key management.
"""

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import base64
from pathlib import Path

# Key file location - generated at install, never in repo
KEY_FILE = "backend/config/license_key.bin"

def ensure_key_exists():
    """Generate encryption key if it doesn't exist with proper permissions."""
    key_path = Path(KEY_FILE)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not key_path.exists():
        # Generate 32-byte key for AES-256
        key = AESGCM.generate_key(bit_length=256)
        
        # Write key with restricted permissions
        with open(key_path, 'wb') as f:
            f.write(key)
        
        # Set file permissions (owner read/write only)
        try:
            os.chmod(key_path, 0o600)
        except OSError:
            # Windows doesn't support chmod the same way
            pass
        
        print(f"Generated new encryption key at {KEY_FILE}")
    
    return key_path

def load_key():
    """Load the encryption key, generating if necessary."""
    key_path = ensure_key_exists()
    with open(key_path, 'rb') as f:
        return f.read()

def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret string and return base64 encoded result."""
    if not plaintext:
        return ""
    
    key = load_key()
    aes = AESGCM(key)
    nonce = os.urandom(12)  # 96-bit nonce for GCM
    ciphertext = aes.encrypt(nonce, plaintext.encode('utf-8'), None)
    
    # Combine nonce + ciphertext and base64 encode
    return base64.b64encode(nonce + ciphertext).decode('ascii')

def decrypt_secret(blob: str) -> str:
    """Decrypt a base64 encoded encrypted secret."""
    if not blob:
        return ""
    
    try:
        key = load_key()
        raw = base64.b64decode(blob)
        nonce, ciphertext = raw[:12], raw[12:]
        aes = AESGCM(key)
        return aes.decrypt(nonce, ciphertext, None).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to decrypt secret: {e}")

def mask_api_key(api_key: str) -> str:
    """Mask API key showing only last 4 characters."""
    if not api_key or len(api_key) < 4:
        return "****"
    
    return "*" * (len(api_key) - 4) + api_key[-4:]

def format_masked_key(api_key: str) -> str:
    """Format masked API key with spacing for UI display."""
    masked = mask_api_key(api_key)
    if len(masked) <= 8:
        return masked
    
    # Add spaces every 4 characters for readability
    return ' '.join([masked[i:i+4] for i in range(0, len(masked), 4)])