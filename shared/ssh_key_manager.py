"""
SSH Key Manager - Generate and manage SSH RSA keys
"""
import os
import subprocess
from typing import Optional, Tuple


def get_default_key_path() -> str:
    """Get the default Ed25519 key path (~/.ssh/id_ed25519)."""
    if os.name == 'nt':
        home = os.environ.get('USERPROFILE', os.path.expanduser('~'))
        return os.path.join(home, '.ssh', 'id_ed25519')
    else:
        return os.path.expanduser('~/.ssh/id_ed25519')


def get_public_key_path(private_key_path: Optional[str] = None) -> str:
    """Get the public key path for a given private key."""
    if private_key_path is None:
        private_key_path = get_default_key_path()
    return private_key_path + '.pub'


def key_exists(key_path: Optional[str] = None) -> bool:
    """
    Check if SSH key exists.

    Args:
        key_path: Path to private key. If None, uses default location.

    Returns:
        bool: True if key exists
    """
    if key_path is None:
        key_path = get_default_key_path()
    return os.path.exists(key_path)


def generate_key(
    key_path: Optional[str] = None,
    comment: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Generate a new Ed25519 key pair using ssh-keygen.

    Ed25519 is preferred over RSA for its superior security and
    smaller key size at equivalent security levels.

    Args:
        key_path: Path to private key. If None, uses default location.
        comment: Comment for the key (optional).

    Returns:
        tuple: (success, message)
    """
    if key_path is None:
        key_path = get_default_key_path()

    # Ensure SSH directory exists
    ssh_dir = os.path.dirname(key_path)
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir, mode=0o700)

    # Check if key already exists
    if os.path.exists(key_path):
        return False, f"Key already exists at {key_path}"

    # Build ssh-keygen command
    cmd = [
        'ssh-keygen',
        '-t', 'ed25519',
        '-f', key_path,
        '-N', ''  # No passphrase
    ]

    if comment:
        cmd.extend(['-C', comment])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return True, f"Ed25519 key generated at {key_path}"
        else:
            return False, f"ssh-keygen failed: {result.stderr}"

    except FileNotFoundError:
        return False, "ssh-keygen not found. Please install OpenSSH."
    except subprocess.TimeoutExpired:
        return False, "ssh-keygen timed out"
    except Exception as e:
        return False, f"Error generating key: {str(e)}"


# Backward-compatible alias
generate_rsa_key = generate_key


def get_public_key_content(key_path: Optional[str] = None) -> Optional[str]:
    """
    Get the public key content.

    Args:
        key_path: Path to private key. If None, uses default location.

    Returns:
        str: Public key content or None if not found
    """
    if key_path is None:
        key_path = get_default_key_path()

    pub_key_path = get_public_key_path(key_path)

    if not os.path.exists(pub_key_path):
        return None

    try:
        with open(pub_key_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception:
        return None


def ensure_key_exists(key_path: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Ensure SSH key exists, generate if not.

    When no key_path is specified, uses the default Ed25519 path.
    Falls back to ~/.ssh/id_rsa for backward compatibility with existing RSA keys.

    Args:
        key_path: Path to private key. If None, uses default location.

    Returns:
        tuple: (success, message, public_key_content)
    """
    if key_path is None:
        key_path = get_default_key_path()
        # Backward compatibility: if id_ed25519 doesn't exist but id_rsa does,
        # reuse the existing RSA key rather than generating a new one
        if not key_exists(key_path):
            rsa_fallback = key_path.replace('id_ed25519', 'id_rsa')
            if key_exists(rsa_fallback):
                key_path = rsa_fallback

    # Check if key exists
    if key_exists(key_path):
        pub_key = get_public_key_content(key_path)
        if pub_key:
            return True, f"Key exists at {key_path}", pub_key
        else:
            return False, f"Private key exists but public key missing at {key_path}.pub", None

    # Generate new key
    success, message = generate_key(key_path)
    if success:
        pub_key = get_public_key_content(key_path)
        return True, message, pub_key
    else:
        return False, message, None
