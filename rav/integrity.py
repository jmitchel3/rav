"""
Integrity verification module for rav.

This module handles Subresource Integrity (SRI) hash verification
for downloaded files. It supports SHA256, SHA384, and SHA512 algorithms.

SRI format: algorithm-base64hash
Example: sha384-Akqfrbj/HpNVo8k11SXBb6TlBWmXXlYQrCSqEWmyKJe+hDm3Z/B2WVG4smwBkRVm
"""

import base64
import hashlib
import pathlib
from typing import Optional, Tuple


class IntegrityError(Exception):
    """Raised when integrity verification fails."""

    pass


class IntegrityVerifier:
    """
    Handles integrity verification for downloaded files using SRI format.
    """

    # Supported hash algorithms
    SUPPORTED_ALGORITHMS = {
        "sha256": hashlib.sha256,
        "sha384": hashlib.sha384,
        "sha512": hashlib.sha512,
    }

    @classmethod
    def parse_integrity(cls, integrity: str) -> Tuple[str, str]:
        """
        Parse an SRI integrity string into algorithm and expected hash.

        Args:
            integrity: SRI integrity string (e.g., "sha384-Akqfrbj/...")

        Returns:
            Tuple of (algorithm, base64_hash)

        Raises:
            IntegrityError: If the integrity string is invalid
        """
        if not integrity or "-" not in integrity:
            raise IntegrityError(f"Invalid integrity format: {integrity}")

        algorithm, base64_hash = integrity.split("-", 1)
        algorithm = algorithm.lower()

        if algorithm not in cls.SUPPORTED_ALGORITHMS:
            raise IntegrityError(
                f"Unsupported algorithm: {algorithm}. "
                f"Supported: {', '.join(cls.SUPPORTED_ALGORITHMS.keys())}"
            )

        return algorithm, base64_hash

    @classmethod
    def compute_hash(cls, file_path: pathlib.Path, algorithm: str) -> str:
        """
        Compute the hash of a file using the specified algorithm.

        Args:
            file_path: Path to the file to hash
            algorithm: Hash algorithm to use (sha256, sha384, sha512)

        Returns:
            Base64-encoded hash string

        Raises:
            IntegrityError: If the algorithm is not supported
            FileNotFoundError: If the file doesn't exist
        """
        if algorithm not in cls.SUPPORTED_ALGORITHMS:
            raise IntegrityError(f"Unsupported algorithm: {algorithm}")

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        hash_func = cls.SUPPORTED_ALGORITHMS[algorithm]()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_func.update(chunk)

        return base64.b64encode(hash_func.digest()).decode("ascii")

    @classmethod
    def verify_integrity(cls, file_path: pathlib.Path, integrity: str) -> bool:
        """
        Verify the integrity of a file against an SRI integrity string.

        Args:
            file_path: Path to the file to verify
            integrity: SRI integrity string (e.g., "sha384-Akqfrbj/...")

        Returns:
            True if integrity check passes, False otherwise

        Raises:
            IntegrityError: If the integrity string is invalid or algorithm unsupported
            FileNotFoundError: If the file doesn't exist
        """
        algorithm, expected_hash = cls.parse_integrity(integrity)
        actual_hash = cls.compute_hash(file_path, algorithm)
        return actual_hash == expected_hash

    @classmethod
    def get_integrity_info(cls, file_path: pathlib.Path, integrity: str) -> dict:
        """
        Get detailed integrity information for debugging.

        Args:
            file_path: Path to the file to verify
            integrity: SRI integrity string

        Returns:
            Dictionary with integrity verification details
        """
        try:
            algorithm, expected_hash = cls.parse_integrity(integrity)
            actual_hash = cls.compute_hash(file_path, algorithm)
            is_valid = actual_hash == expected_hash

            return {
                "algorithm": algorithm,
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
                "is_valid": is_valid,
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size if file_path.exists() else None,
            }
        except Exception as e:
            return {
                "error": str(e),
                "file_path": str(file_path),
                "integrity": integrity,
            }


def verify_file_integrity(file_path: pathlib.Path, integrity: Optional[str]) -> bool:
    """
    Convenience function to verify file integrity.

    Args:
        file_path: Path to the file to verify
        integrity: SRI integrity string, or None to skip verification

    Returns:
        True if integrity check passes or no integrity specified, False otherwise
    """
    if not integrity:
        return True

    try:
        return IntegrityVerifier.verify_integrity(file_path, integrity)
    except Exception:
        return False
