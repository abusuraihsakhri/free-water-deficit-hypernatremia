"""Pattern-based identifier checks and in-memory HMAC-chained audit entries.

PHI detection is best-effort only; it is not HIPAA de-identification.
Audit entries are not durable across process restarts.
"""
import hashlib
import hmac
import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

PHI_PATTERNS = [
    re.compile(r"\bMRN[:#\s-]*\d{4,10}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    re.compile(r"\b(?:DOB|Date of Birth)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE),
    re.compile(r"\b(?:Patient\s+Name|Patient)[:\s]+[A-Z][a-z]+\s+[A-Z][a-z]+\b", re.IGNORECASE),
    re.compile(r"\b(?:John\s+Doe|Jane\s+Smith|Alice\s+Johnson)\b", re.IGNORECASE),
]


class SecurityException(Exception):
    """Possible identifying material in input."""


class ResourceLimitExceededException(Exception):
    """Resource budget exceeded."""


def assert_no_phi(text: str) -> None:
    for pattern in PHI_PATTERNS:
        if pattern.search(str(text or "")):
            raise SecurityException("Input may contain a patient identifier; remove it before continuing.")


class PHIGuard:
    assert_no_phi = staticmethod(assert_no_phi)

    @staticmethod
    def redact_phi(text: str) -> str:
        value = str(text)
        for pattern in PHI_PATTERNS:
            value = pattern.sub("[REDACTED_IDENTIFIER]", value)
        return value


class AuditTrail:
    """Process-local HMAC chain with verification of entry content and order."""

    def __init__(self, secret_key: Optional[str] = None):
        configured = secret_key if secret_key is not None else os.getenv("AUDIT_SECRET_KEY", "")
        # No default key checked into the repository.
        self.secret_key = configured.encode("utf-8") if configured else os.urandom(32)
        self.logs: List[Dict[str, Any]] = []

    @staticmethod
    def _signed_text(entry):
        return "|".join(str(entry[key]) for key in (
            "audit_id", "timestamp", "actor", "actor_tier", "event_type",
            "payload_hash", "prev_hash"
        ))

    def log(self, actor: str, actor_tier: str, event_type: str, details: Dict[str, Any]) -> Dict[str, Any]:
        assert_no_phi(json.dumps(details, sort_keys=True))
        for label in (actor, actor_tier, event_type):
            assert_no_phi(label)
        last_hash = self.logs[-1]["current_hash"] if self.logs else "GENESIS_BLOCK_0000000000000000"
        entry = {
            "audit_id": f"AUDIT-{time.time_ns()}-{len(self.logs)+1}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "actor_tier": actor_tier,
            "event_type": event_type,
            "payload_hash": hashlib.sha256(json.dumps(details, sort_keys=True).encode("utf-8")).hexdigest(),
            "prev_hash": last_hash,
        }
        entry["current_hash"] = hmac.new(
            self.secret_key, self._signed_text(entry).encode("utf-8"), hashlib.sha256
        ).hexdigest()
        self.logs.append(entry)
        return entry

    def verify_integrity(self) -> bool:
        previous = "GENESIS_BLOCK_0000000000000000"
        try:
            for entry in self.logs:
                if entry["prev_hash"] != previous:
                    return False
                expected = hmac.new(self.secret_key, self._signed_text(entry).encode("utf-8"),
                                    hashlib.sha256).hexdigest()
                if not hmac.compare_digest(expected, entry["current_hash"]):
                    return False
                previous = entry["current_hash"]
        except (KeyError, TypeError, ValueError):
            return False
        return True

    def get_trail(self) -> List[Dict[str, Any]]:
        return self.logs


GLOBAL_AUDIT = AuditTrail()


class AuditLogger:
    log = staticmethod(GLOBAL_AUDIT.log)
    get_trail = staticmethod(GLOBAL_AUDIT.get_trail)
    verify_integrity = staticmethod(GLOBAL_AUDIT.verify_integrity)


class ActionExecutor:
    @staticmethod
    def execute_with_audit(actor: str, actor_tier: str, action_type: str, fn, *args, **kwargs):
        result = fn(*args, **kwargs)
        AuditLogger.log(actor, actor_tier, action_type, {"status": "SUCCESS"})
        return result
