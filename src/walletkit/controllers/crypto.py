"""Crypto controller implementation."""
import base64
import hashlib
import json
import time
from typing import Any, Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from walletkit.constants.crypto import CRYPTO_CLIENT_SEED, CRYPTO_CONTEXT, CRYPTO_JWT_TTL
from walletkit.controllers.keychain import KeyChain
from walletkit.utils.crypto_utils import (
    BASE64URL,
    TYPE_0,
    TYPE_1,
    TYPE_2,
    decrypt_message,
    derive_sym_key,
    encode_type_two_envelope,
    decode_type_two_envelope,
    encrypt_message,
    generate_key_pair,
    generate_random_bytes32,
    get_payload_sender_public_key,
    get_payload_type,
    hash_key,
)


class Crypto:
    """Crypto controller for encryption/decryption and key management."""

    def __init__(
        self,
        storage: Any,  # IKeyValueStorage
        logger: Any,  # Logger
        keychain: Optional[KeyChain] = None,
        storage_prefix: str = "wc@2:core:",
    ) -> None:
        """Initialize Crypto controller.
        
        Args:
            storage: Storage backend
            logger: Logger instance
            keychain: Optional keychain instance
            storage_prefix: Storage key prefix
        """
        self.name = CRYPTO_CONTEXT
        self.storage = storage
        self.logger = logger
        self.storage_prefix = storage_prefix
        self.keychain = keychain or KeyChain(storage, storage_prefix)
        self.random_session_identifier = generate_random_bytes32()
        self._initialized = False
        self._client_id: Optional[str] = None

    async def init(self) -> None:
        """Initialize crypto controller."""
        if not self._initialized:
            await self.keychain.init()
            self._initialized = True

    def has_keys(self, tag: str) -> bool:
        """Check if key exists.
        
        Args:
            tag: Key tag
            
        Returns:
            True if key exists
        """
        self._check_initialized()
        return self.keychain.has(tag)

    async def get_client_id(self) -> str:
        """Get or generate client ID.
        
        Returns:
            Client ID string
        """
        self._check_initialized()
        if self._client_id:
            return self._client_id

        # WalletConnect relay-auth uses an "iss" that encodes the signing public key.
        # We implement the common did:key encoding for Ed25519 public keys.
        seed_hex = await self._get_client_seed()
        _, iss = self._get_relay_auth_keypair_and_iss(seed_hex)
        self._client_id = iss
        return iss

    async def generate_key_pair(self) -> str:
        """Generate X25519 key pair.
        
        Returns:
            Public key (hex)
        """
        self._check_initialized()
        key_pair = generate_key_pair()
        # Store private key, return public key
        await self._set_private_key(key_pair["publicKey"], key_pair["privateKey"])
        return key_pair["publicKey"]

    async def sign_jwt(self, aud: str) -> str:
        """Sign JWT for relay authentication.
        
        Args:
            aud: Audience (relay URL)
            
        Returns:
            JWT string
        
        Note:
            WalletConnect relay expects an `auth` JWT (query param) signed by the client's
            relay-auth key pair. We implement a minimal compatible EdDSA (Ed25519) JWT.
        """
        self._check_initialized()
        seed_hex = await self._get_client_seed()
        private_key, iss = self._get_relay_auth_keypair_and_iss(seed_hex)

        iat = int(time.time())
        exp = iat + int(CRYPTO_JWT_TTL / 1000)
        sub = self.random_session_identifier

        header = {"alg": "EdDSA", "typ": "JWT"}
        payload = {"iss": iss, "sub": sub, "aud": aud, "iat": iat, "exp": exp}

        signing_input = f"{self._b64url_json(header)}.{self._b64url_json(payload)}".encode("utf-8")
        signature = private_key.sign(signing_input)
        token = f"{signing_input.decode('utf-8')}.{self._b64url_encode(signature)}"
        return token

    async def generate_shared_key(
        self,
        self_public_key: str,
        peer_public_key: str,
        override_topic: Optional[str] = None,
    ) -> str:
        """Generate shared symmetric key from key pair.
        
        Args:
            self_public_key: Self public key (hex)
            peer_public_key: Peer public key (hex)
            override_topic: Optional topic override
            
        Returns:
            Topic (derived from shared key or override)
        """
        self._check_initialized()
        self_private_key = self._get_private_key(self_public_key)
        sym_key = derive_sym_key(self_private_key, peer_public_key)
        return await self.set_sym_key(sym_key, override_topic)

    async def set_sym_key(
        self, sym_key: str, override_topic: Optional[str] = None
    ) -> str:
        """Set symmetric key in keychain.
        
        Args:
            sym_key: Symmetric key (hex)
            override_topic: Optional topic override
            
        Returns:
            Topic
        """
        self._check_initialized()
        topic = override_topic or hash_key(sym_key)
        await self.keychain.set(topic, sym_key)
        return topic

    async def delete_key_pair(self, public_key: str) -> None:
        """Delete key pair.
        
        Args:
            public_key: Public key
        """
        self._check_initialized()
        await self.keychain.delete(public_key)

    async def delete_sym_key(self, topic: str) -> None:
        """Delete symmetric key.
        
        Args:
            topic: Topic
        """
        self._check_initialized()
        await self.keychain.delete(topic)

    async def encode(
        self,
        topic: str,
        payload: dict[str, Any],
        opts: Optional[dict[str, Any]] = None,
    ) -> str:
        """Encode/encrypt a payload.
        
        Args:
            topic: Topic for encryption
            payload: JSON-RPC payload
            opts: Encoding options
            
        Returns:
            Encoded/encrypted message
        """
        self._check_initialized()
        if opts is None:
            opts = {}
        
        message = json.dumps(payload)
        encoding = opts.get("encoding", BASE64URL)
        
        # Check if type 2 envelope (unencrypted)
        if opts.get("type") == TYPE_2:
            return encode_type_two_envelope(message, encoding)
        
        # Check if type 1 envelope (needs public keys)
        if opts.get("type") == TYPE_1:
            self_public_key = opts.get("senderPublicKey")
            peer_public_key = opts.get("receiverPublicKey")
            if not self_public_key or not peer_public_key:
                raise ValueError("Type 1 envelope requires sender and receiver public keys")
            # Generate shared key and update topic
            topic = await self.generate_shared_key(self_public_key, peer_public_key)
        
        # Get symmetric key for topic
        sym_key = self._get_sym_key(topic)
        type_val = opts.get("type", TYPE_0)
        sender_public_key = opts.get("senderPublicKey")
        
        return encrypt_message(
            sym_key,
            message,
            type_val=type_val,
            sender_public_key=sender_public_key,
            encoding=encoding,
        )

    async def decode(
        self,
        topic: str,
        encoded: str,
        opts: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Decode/decrypt a message.
        
        Args:
            topic: Topic for decryption
            encoded: Encoded/encrypted message
            opts: Decoding options
            
        Returns:
            Decoded payload
        """
        self._check_initialized()
        if opts is None:
            opts = {}
        
        encoding = opts.get("encoding", BASE64URL)
        
        # Check payload type
        payload_type = get_payload_type(encoded, encoding)
        
        # Type 2 envelope (unencrypted)
        if payload_type == TYPE_2:
            message = decode_type_two_envelope(encoded, encoding)
            return json.loads(message)
        
        # Type 1 envelope (needs public keys)
        if payload_type == TYPE_1:
            sender_public_key = get_payload_sender_public_key(encoded, encoding)
            receiver_public_key = opts.get("receiverPublicKey")
            if not sender_public_key or not receiver_public_key:
                raise ValueError("Type 1 envelope requires sender and receiver public keys")
            # Generate shared key and update topic
            topic = await self.generate_shared_key(receiver_public_key, sender_public_key)
        
        try:
            sym_key = self._get_sym_key(topic)
            message = decrypt_message(sym_key, encoded, encoding)
            return json.loads(message)
        except Exception as error:
            client_id = await self.get_client_id()
            self.logger.error(
                f"Failed to decode message from topic: '{topic}', clientId: '{client_id}'"
            )
            self.logger.error(str(error))
            raise

    def get_payload_type(self, encoded: str, encoding: str = BASE64URL) -> int:
        """Get payload type from encoded message.
        
        Args:
            encoded: Encoded message
            encoding: Encoding type
            
        Returns:
            Payload type
        """
        return get_payload_type(encoded, encoding)

    def get_payload_sender_public_key(
        self, encoded: str, encoding: str = BASE64URL
    ) -> Optional[str]:
        """Get sender public key from encoded message.
        
        Args:
            encoded: Encoded message
            encoding: Encoding type
            
        Returns:
            Sender public key (hex) or None
        """
        return get_payload_sender_public_key(encoded, encoding)

    # ---------- Private ----------------------------------------------- #

    @staticmethod
    def _b64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

    @classmethod
    def _b64url_json(cls, obj: dict[str, Any]) -> str:
        raw = json.dumps(obj, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return cls._b64url_encode(raw)

    @staticmethod
    def _b58encode(data: bytes) -> str:
        """Minimal base58btc encoder (no checksum)."""
        alphabet = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        n = int.from_bytes(data, "big")
        out = bytearray()
        while n > 0:
            n, r = divmod(n, 58)
            out.append(alphabet[r])
        # preserve leading zeros
        pad = 0
        for b in data:
            if b == 0:
                pad += 1
            else:
                break
        return (alphabet[0:1] * pad + out[::-1]).decode("ascii")

    def _get_relay_auth_keypair_and_iss(self, seed_hex: str) -> tuple[Ed25519PrivateKey, str]:
        """Derive a deterministic Ed25519 key pair for relay auth from the client seed."""
        try:
            seed_bytes = bytes.fromhex(seed_hex)
        except Exception:
            seed_bytes = seed_hex.encode("utf-8")

        # Ensure 32 bytes for Ed25519 private key
        if len(seed_bytes) != 32:
            seed_bytes = hashlib.sha256(seed_bytes).digest()

        private_key = Ed25519PrivateKey.from_private_bytes(seed_bytes)
        public_key_bytes = private_key.public_key().public_bytes_raw()

        # did:key for Ed25519 uses multicodec prefix 0xed01
        multicodec = b"\xed\x01" + public_key_bytes
        did = "did:key:z" + self._b58encode(multicodec)
        return private_key, did

    async def _set_private_key(self, public_key: str, private_key: str) -> str:
        """Set private key in keychain.
        
        Args:
            public_key: Public key
            private_key: Private key
            
        Returns:
            Public key
        """
        await self.keychain.set(public_key, private_key)
        return public_key

    def _get_private_key(self, public_key: str) -> str:
        """Get private key from keychain.
        
        Args:
            public_key: Public key
            
        Returns:
            Private key
        """
        return self.keychain.get(public_key)

    async def _get_client_seed(self) -> str:
        """Get or generate client seed.
        
        Returns:
            Client seed (hex)
        """
        try:
            seed = self.keychain.get(CRYPTO_CLIENT_SEED)
        except KeyError:
            seed = generate_random_bytes32()
            await self.keychain.set(CRYPTO_CLIENT_SEED, seed)
        return seed

    def _get_sym_key(self, topic: str) -> str:
        """Get symmetric key from keychain.
        
        Args:
            topic: Topic
            
        Returns:
            Symmetric key
        """
        return self.keychain.get(topic)

    def _check_initialized(self) -> None:
        """Check if crypto is initialized."""
        if not self._initialized:
            raise RuntimeError(f"{self.name} not initialized. Call init() first.")

