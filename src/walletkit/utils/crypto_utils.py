"""Crypto utility functions."""
import base64
import secrets
from typing import Optional

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# Constants
TYPE_0 = 0
TYPE_1 = 1
TYPE_2 = 2
KEY_LENGTH = 32
IV_LENGTH = 12
BASE16 = "base16"
BASE64 = "base64"
BASE64URL = "base64url"


def bytes_to_hex(data: bytes) -> str:
    """Convert bytes to hex string."""
    return data.hex()


def hex_to_bytes(hex_str: str) -> bytes:
    """Convert hex string to bytes."""
    return bytes.fromhex(hex_str)


def generate_key_pair() -> dict[str, str]:
    """Generate X25519 key pair.
    
    Returns:
        Dict with 'privateKey' and 'publicKey' as hex strings
    """
    private_key = X25519PrivateKey.generate()
    public_key = private_key.public_key()
    
    return {
        "privateKey": bytes_to_hex(private_key.private_bytes_raw()),
        "publicKey": bytes_to_hex(public_key.public_bytes_raw()),
    }


def generate_random_bytes32() -> str:
    """Generate random 32 bytes as hex string.
    
    Returns:
        Random 32 bytes as hex string
    """
    random_bytes = secrets.token_bytes(KEY_LENGTH)
    return bytes_to_hex(random_bytes)


def derive_sym_key(private_key_a: str, public_key_b: str) -> str:
    """Derive symmetric key from two X25519 keys.
    
    Args:
        private_key_a: Private key A (hex)
        public_key_b: Public key B (hex)
        
    Returns:
        Derived symmetric key (hex)
    """
    priv_key = X25519PrivateKey.from_private_bytes(hex_to_bytes(private_key_a))
    pub_key = X25519PublicKey.from_public_bytes(hex_to_bytes(public_key_b))
    
    shared_key = priv_key.exchange(pub_key)
    
    # HKDF to derive symmetric key
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=KEY_LENGTH,
        salt=None,
        info=None,
    )
    sym_key = hkdf.derive(shared_key)
    
    return bytes_to_hex(sym_key)


def hash_key(key: str) -> str:
    """Hash a key using SHA-256.
    
    Args:
        key: Key to hash (hex)
        
    Returns:
        Hashed key (hex)
    """
    key_bytes = hex_to_bytes(key)
    digest = hashes.Hash(hashes.SHA256())
    digest.update(key_bytes)
    hashed = digest.finalize()
    return bytes_to_hex(hashed)


def hash_message(message: str) -> str:
    """Hash a message using SHA-256.
    
    Args:
        message: Message to hash (UTF-8 string)
        
    Returns:
        Hashed message (hex)
    """
    message_bytes = message.encode("utf-8")
    digest = hashes.Hash(hashes.SHA256())
    digest.update(message_bytes)
    hashed = digest.finalize()
    return bytes_to_hex(hashed)


def encode_type_byte(type_val: int) -> bytes:
    """Encode type as byte.
    
    Args:
        type_val: Type value
        
    Returns:
        Type as bytes
    """
    # WalletConnect JS uses uint8arrays base10 encoding which yields a single raw byte
    # for small integers 0/1/2. We match that wire format here.
    if type_val < 0 or type_val > 255:
        raise ValueError("type_val must fit in a single byte")
    return int(type_val).to_bytes(1, "big")


def decode_type_byte(byte_data: bytes) -> int:
    """Decode type from byte.
    
    Args:
        byte_data: Type byte
        
    Returns:
        Type value
    """
    if not byte_data:
        raise ValueError("byte_data is empty")
    # Primary: raw byte (WalletConnect JS / uint8arrays base10)
    if len(byte_data) == 1:
        return byte_data[0]
    # Fallback: some older code encoded ascii digits; keep a safe fallback.
    try:
        s = byte_data.decode("utf-8")
        if s.isdigit():
            return int(s)
    except Exception:
        pass
    raise ValueError("Invalid type byte")


def to_base64url(base64_str: str) -> str:
    """Convert base64 to base64url.
    
    Args:
        base64_str: Base64 string
        
    Returns:
        Base64URL string
    """
    return base64_str.replace("+", "-").replace("/", "_").replace("=", "")


def from_base64url(base64url_str: str) -> str:
    """Convert base64url to base64.
    
    Args:
        base64url_str: Base64URL string
        
    Returns:
        Base64 string
    """
    base64_str = base64url_str.replace("-", "+").replace("_", "/")
    padding = (4 - (len(base64_str) % 4)) % 4
    return base64_str + "=" * padding


def serialize_envelope(
    type_byte: bytes,
    sealed: bytes,
    iv: bytes,
    sender_public_key: Optional[bytes] = None,
) -> str:
    """Serialize envelope to base64.
    
    Args:
        type_byte: Type byte
        sealed: Sealed (encrypted) data
        iv: Initialization vector
        sender_public_key: Optional sender public key
        
    Returns:
        Base64 encoded envelope
    """
    if decode_type_byte(type_byte) == TYPE_2:
        return base64.b64encode(type_byte + sealed).decode("utf-8")
    
    if decode_type_byte(type_byte) == TYPE_1:
        if sender_public_key is None:
            raise ValueError("Missing sender public key for type 1 envelope")
        return base64.b64encode(
            type_byte + sender_public_key + iv + sealed
        ).decode("utf-8")
    
    # TYPE_0 (default)
    return base64.b64encode(type_byte + iv + sealed).decode("utf-8")


def deserialize_envelope(
    encoded: str, encoding: str = BASE64
) -> dict[str, bytes]:
    """Deserialize envelope from base64.
    
    Args:
        encoded: Encoded envelope
        encoding: Encoding type (base64 or base64url)
        
    Returns:
        Dict with type, sealed, iv, and optionally sender_public_key
    """
    if encoding == BASE64URL:
        encoded = from_base64url(encoded)
    
    bytes_data = base64.b64decode(encoded)
    
    type_byte = bytes_data[0:1]
    type_val = decode_type_byte(type_byte)
    
    if type_val == TYPE_1:
        slice1 = 1
        slice2 = slice1 + KEY_LENGTH
        slice3 = slice2 + IV_LENGTH
        sender_public_key = bytes_data[slice1:slice2]
        iv = bytes_data[slice2:slice3]
        sealed = bytes_data[slice3:]
        return {
            "type": type_byte,
            "sealed": sealed,
            "iv": iv,
            "sender_public_key": sender_public_key,
        }
    
    if type_val == TYPE_2:
        sealed = bytes_data[1:]
        # IV not used but required for structure
        iv = secrets.token_bytes(IV_LENGTH)
        return {
            "type": type_byte,
            "sealed": sealed,
            "iv": iv,
        }
    
    # TYPE_0 (default)
    slice1 = 1
    slice2 = slice1 + IV_LENGTH
    iv = bytes_data[slice1:slice2]
    sealed = bytes_data[slice2:]
    return {
        "type": type_byte,
        "sealed": sealed,
        "iv": iv,
    }


def encrypt_message(
    sym_key: str,
    message: str,
    type_val: int = TYPE_0,
    sender_public_key: Optional[str] = None,
    iv: Optional[str] = None,
    encoding: str = BASE64,
) -> str:
    """Encrypt a message.
    
    Args:
        sym_key: Symmetric key (hex)
        message: Message to encrypt (UTF-8 string)
        type_val: Envelope type
        sender_public_key: Optional sender public key (hex)
        iv: Optional IV (hex)
        encoding: Encoding type (base64 or base64url)
        
    Returns:
        Encrypted message (base64/base64url)
    """
    if type_val == TYPE_1 and sender_public_key is None:
        raise ValueError("Missing sender public key for type 1 envelope")
    
    type_byte = encode_type_byte(type_val)
    sender_pub_key_bytes = (
        hex_to_bytes(sender_public_key) if sender_public_key else None
    )
    
    if iv is None:
        iv_bytes = secrets.token_bytes(IV_LENGTH)
    else:
        iv_bytes = hex_to_bytes(iv)
    
    key_bytes = hex_to_bytes(sym_key)
    message_bytes = message.encode("utf-8")
    
    # Encrypt with ChaCha20-Poly1305
    cipher = ChaCha20Poly1305(key_bytes)
    sealed = cipher.encrypt(iv_bytes, message_bytes, None)
    
    result = serialize_envelope(type_byte, sealed, iv_bytes, sender_pub_key_bytes)
    
    if encoding == BASE64URL:
        return to_base64url(result)
    return result


def decrypt_message(
    sym_key: str,
    encoded: str,
    encoding: str = BASE64,
) -> str:
    """Decrypt a message.
    
    Args:
        sym_key: Symmetric key (hex)
        encoded: Encrypted message (base64/base64url)
        encoding: Encoding type (base64 or base64url)
        
    Returns:
        Decrypted message (UTF-8 string)
    """
    key_bytes = hex_to_bytes(sym_key)
    envelope = deserialize_envelope(encoded, encoding)
    
    sealed = envelope["sealed"]
    iv = envelope["iv"]
    
    # Decrypt with ChaCha20-Poly1305
    cipher = ChaCha20Poly1305(key_bytes)
    try:
        message_bytes = cipher.decrypt(iv, sealed, None)
        return message_bytes.decode("utf-8")
    except Exception as e:
        raise ValueError("Failed to decrypt") from e


def encode_type_two_envelope(message: str, encoding: str = BASE64) -> str:
    """Encode type 2 envelope (unencrypted).
    
    Args:
        message: Message to encode
        encoding: Encoding type
        
    Returns:
        Encoded envelope
    """
    type_byte = encode_type_byte(TYPE_2)
    sealed = message.encode("utf-8")
    iv = secrets.token_bytes(IV_LENGTH)  # Not used but required for structure
    
    result = serialize_envelope(type_byte, sealed, iv)
    
    if encoding == BASE64URL:
        return to_base64url(result)
    return result


def decode_type_two_envelope(encoded: str, encoding: str = BASE64) -> str:
    """Decode type 2 envelope (unencrypted).
    
    Args:
        encoded: Encoded envelope
        encoding: Encoding type
        
    Returns:
        Decoded message
    """
    envelope = deserialize_envelope(encoded, encoding)
    sealed = envelope["sealed"]
    return sealed.decode("utf-8")


def get_payload_type(encoded: str, encoding: str = BASE64) -> int:
    """Get payload type from encoded message.
    
    Args:
        encoded: Encoded message
        encoding: Encoding type
        
    Returns:
        Payload type
    """
    envelope = deserialize_envelope(encoded, encoding)
    return decode_type_byte(envelope["type"])


def get_payload_sender_public_key(encoded: str, encoding: str = BASE64) -> Optional[str]:
    """Get sender public key from encoded message.
    
    Args:
        encoded: Encoded message
        encoding: Encoding type
        
    Returns:
        Sender public key (hex) or None
    """
    envelope = deserialize_envelope(encoded, encoding)
    sender_pub_key = envelope.get("sender_public_key")
    if sender_pub_key:
        return bytes_to_hex(sender_pub_key)
    return None

