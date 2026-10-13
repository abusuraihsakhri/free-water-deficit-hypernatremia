import pytest
from fastapi import HTTPException
from agents.api import WaterDeficitRequest, api_water_deficit
from agents.base import AuditTrail, SecurityException


def test_api_calculator():
    result = api_water_deficit(WaterDeficitRequest(
        weight_kg=60, serum_sodium=166, tbw_fraction=0.5))
    assert result["free_water_deficit_l"] == pytest.approx(5.5714285714)


def test_api_invalid_target():
    with pytest.raises(HTTPException) as exc:
        api_water_deficit(WaterDeficitRequest(
            weight_kg=60, serum_sodium=166, tbw_fraction=0.5, target_sodium=180))
    assert exc.value.status_code == 422


def test_hmac_detects_changed_entry():
    trail = AuditTrail(secret_key="test-only-secret")
    trail.log("test", "worker", "TEST_EVENT", {"status": "ok"})
    assert trail.verify_integrity()
    trail.logs[0]["event_type"] = "CHANGED"
    assert not trail.verify_integrity()


def test_hmac_detects_spliced_chain():
    trail = AuditTrail(secret_key="test-only-secret")
    trail.log("test", "worker", "TEST_EVENT", {"status": "ok"})
    trail.log("test", "worker", "TEST_EVENT", {"status": "ok"})
    assert trail.verify_integrity()
    trail.logs.pop(0)
    assert not trail.verify_integrity()


def test_phi_error_does_not_echo_raw_identifier():
    trail = AuditTrail(secret_key="test-only-secret")
    with pytest.raises(SecurityException) as exc:
        trail.log("test", "worker", "TEST_EVENT", {"case": "MRN-994827"})
    assert "994827" not in str(exc.value)
