"""Mock OTP service for phone verification in BLH Voice Agent POC."""

from __future__ import annotations

# In-memory mock store: { phone: "1234" }
_otp_store: dict[str, str] = {}
MOCK_OTP = "1234"


def send_otp(phone: str) -> dict:
    """Store and print a mock 4-digit OTP for the given phone number."""
    clean_phone = phone.strip()
    _otp_store[clean_phone] = MOCK_OTP

    print(f"\n[MOCK SMS to {clean_phone}] Your BLH verification code is {MOCK_OTP}\n")
    return {
        "success": True,
        "message": f"A verification code has been sent to {clean_phone}.",
    }


def verify_otp(phone: str, otp: str) -> dict:
    """Verify the provided OTP against the stored code for the phone number."""
    clean_phone = phone.strip()
    clean_otp = otp.strip()

    expected = _otp_store.get(clean_phone, MOCK_OTP)
    if clean_otp == expected or clean_otp == MOCK_OTP:
        return {
            "verified": True,
            "message": "Phone number verified successfully.",
        }

    return {
        "verified": False,
        "message": "Incorrect verification code.",
    }
