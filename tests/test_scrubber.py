from __future__ import annotations

import pytest

from app.services.pii_scrubber import PlaceholderVault, scrub_text


def scrub(text: str) -> str:
    return scrub_text(text, PlaceholderVault())


def test_email_is_replaced_and_consistent() -> None:
    out = scrub("Pay bilal.test@example.com or bilal.test@example.com")
    assert out.count("<EMAIL_1>") == 2
    assert "example.com" not in out


@pytest.mark.parametrize(
    "raw",
    [
        "Phone: +44 7700 900123",
        "Cell # 0300-1234567",
        "Mobile: +91 98220 43210",
    ],
)
def test_labelled_phones_are_replaced(raw: str) -> None:
    out = scrub(raw)
    assert "<PHONE_" in out
    assert "900123" not in out
    assert "1234567" not in out
    assert "43210" not in out


def test_unlabelled_phone_formats() -> None:
    for raw in ("Call +1 (512) 555-0148", "Reach 416-555-0177", "Dial (0315) 1234567"):
        out = scrub(raw)
        assert "<PHONE_" in out, raw


def test_iban_labelled_and_plain() -> None:
    out = scrub("IBAN: GB82 WEST 1234 5698 7654 32")
    assert "GB82" not in out and "<IBAN_1>" in out
    out = scrub("Transfer to PK36SCBL0000001123456702")
    assert "PK36SCBL" not in out and "<IBAN_1>" in out


def test_cards_full_vs_masked() -> None:
    out = scrub("Charge 4111 1111 1111 1111")
    assert "<CARD_1>" in out and "4111" not in out
    assert scrub("Card xxxx2070") == "Card xxxx2070"
    assert scrub("Card ending 4532") == "Card ending 4532"
    assert scrub("****6677") == "****6677"
    assert scrub("XXXXXX4321") == "XXXXXX4321"
    assert "<CARD_1>" in scrub("Linked Card: 521234******2070")


def test_national_ids() -> None:
    assert "<CNIC_1>" in scrub("CNIC No 35202-1234567-1")
    assert "<SSN_1>" in scrub("SSN on file: 123-45-6789")
    assert "<SIN_1>" in scrub("SIN: 046454286")
    assert "<NI_1>" in scrub("NI Number: AB123456C")
    assert "<PAN_1>" in scrub("PAN: ABCDE1234F")
    assert "<AADHAAR_1>" in scrub("Aadhaar: 1234 5678 9012")
    assert "<TAX_ID_1>" in scrub("Steuer-ID: 12 345 678 903")


def test_bank_routing() -> None:
    assert "<SORT_CODE_1>" in scrub("Sort Code: 40-22-19 (402219)")
    assert "<BIC_1>" in scrub("BIC: NWBKGB2LXXX")
    assert "<ROUTING_1>" in scrub("Routing Number: 021000021")
    assert "<IFSC_1>" in scrub("IFSC: SVBL0001234")
    assert "<MICR_1>" in scrub("MICR: 411240012")
    transit = scrub("Transit: 30800 Institution: 828")
    assert "<TRANSIT_1>" in transit and "<INSTITUTION_1>" in transit
    assert "<BLZ_1>" in scrub("BLZ: 37040044")


def test_account_numbers() -> None:
    assert "<ACCOUNT_ID_1>" in scrub("A/C No: 0011223344556677")
    assert "<ACCOUNT_ID_1>" in scrub("Account Number: 55667788")
    assert "<ACCOUNT_ID_1>" in scrub("ACC 8899-0011-2233-4455")
    assert "<ACCOUNT_ID_1>" in scrub("Consumer Number: 40012345678901")


def test_reference_ids() -> None:
    assert "<REF_" in scrub("Trace 662209118845")
    assert "<REF_" in scrub("Order 402-8871253-1123456")
    assert "<REF_" in scrub("REF 20260401778812")
    assert "<REF_" in scrub("Cheque No 0044521")
    assert "<REF_" in scrub("Image REF 20260422-114455")
    ids = scrub("Transaction IDs: 8XJ22190T7002841M, 4PL80331B2114902K")
    assert "<REF_" in ids and "8XJ22190" not in ids


def test_address_and_wallet_and_ip() -> None:
    out = scrub("Address: Flat 3, 82 Church Lane, Manchester M20 4WX, UK")
    assert out == "Address: <ADDRESS_1>"
    assert "<WALLET_ID_1>" in scrub("Wallet ID,bilalhk91")
    assert "<IP_1>" in scrub("Login IP (last): 39.51.202.114")


def test_preserves_analytical_content() -> None:
    raw = (
        "Netflix.com AMAZON.CO.UK TESCO STORES 3421 01 Apr 2026 "
        "+£2,450.00 £3,120.44 Bilal Hassan Khan"
    )
    assert scrub(raw) == raw


def test_embedded_identifiers_do_not_destroy_meaning() -> None:
    raw = (
        "Incoming fund transfer from Gulf Freelance Portal LLC "
        "IBAN PK36SCBL0000001123456702 Invoice GFP-2026-0412"
    )
    out = scrub(raw)
    assert "Gulf Freelance Portal LLC" in out
    assert "Incoming fund transfer from" in out
    assert "Invoice" in out
    assert "<IBAN_1>" in out
    assert "<REF_1>" in out


def test_same_value_same_placeholder_across_calls() -> None:
    vault = PlaceholderVault()
    first = scrub_text("Email a@example.com", vault)
    second = scrub_text("Again a@example.com", vault)
    assert "<EMAIL_1>" in first and "<EMAIL_1>" in second


def test_scrubbing_is_idempotent() -> None:
    raw = (
        "Phone: +44 7700 900123 | IBAN: GB82 WEST 1234 5698 7654 32 | "
        "Card 4111 1111 1111 1111 | Trace 662209118845"
    )
    vault = PlaceholderVault()
    once = scrub_text(raw, vault)
    twice = scrub_text(once, vault)
    assert once == twice
