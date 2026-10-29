from __future__ import annotations

import re
from dataclasses import dataclass

"""Local, deterministic PII scrubber for financial statements.

Design goals:
* High recall for identifiers (IBAN, cards, national IDs, phones, emails,
  routing data, reference/trace IDs, addresses, wallet/UPI handles).
* High precision for analytical content (names, merchants, dates, amounts,
  balances, currencies, descriptions) — no blanket "delete long numbers".
* Consistent placeholders across files within one run, e.g. the same email is
  always ``<EMAIL_1>`` so cross-file analysis still works.

All matching happens locally. Nothing here performs network I/O.
"""


_WALLET_DOMAINS = {
    "okaxis",
    "okhdfc",
    "okicici",
    "oksbi",
    "paytm",
    "ybl",
    "ibl",
    "axl",
    "upi",
    "nayapay",
    "easypaisa",
    "jazzcash",
}

# Curated ISO-3166 alpha-2 codes used to reduce BIC false positives on ordinary
# uppercase words (a bare "8 uppercase letters" rule would eat "CRESCENT").
_BIC_COUNTRIES = set(
    "US GB DE CA IN PK AE SG AU CH FR IT ES NL BE SE NO DK FI IE JP CN HK NZ "
    "ZA BR MX TR SA QA KW BH MY TH ID PH VN KR TW LU AT PT GR PL CZ HU RO RU "
    "UA IL EG NG KE GH MU LK BD NP".split()
)

_DIGITS_ONLY_TYPES = {
    "CARD",
    "ACCOUNT_ID",
    "PHONE",
    "CNIC",
    "SSN",
    "SIN",
    "AADHAAR",
    "TAX_ID",
    "ROUTING",
    "SORT_CODE",
    "MICR",
    "TRANSIT",
    "INSTITUTION",
    "BLZ",
}
_UPPER_TYPES = {"IBAN", "NI", "PAN", "BIC", "IFSC"}


@dataclass
class ScrubStats:
    occurrences: dict[str, int]
    unique_by_type: dict[str, int]


class PlaceholderVault:
    """Maps identifier values to stable placeholder tokens for one scrub run."""

    def __init__(self) -> None:
        self._tokens: dict[tuple[str, str], str] = {}
        self._counters: dict[str, int] = {}
        self._occurrences: dict[str, int] = {}

    @staticmethod
    def _normalize(ptype: str, value: str) -> str:
        value = value.strip()
        if ptype in _DIGITS_ONLY_TYPES:
            digits = re.sub(r"\D", "", value)
            return digits or value.lower()
        if ptype == "IBAN":
            return re.sub(r"[ \t]", "", value).upper()
        if ptype in _UPPER_TYPES:
            return re.sub(r"[ \t]", "", value).upper()
        if ptype == "IP":
            return value
        if ptype in {"EMAIL", "PAYMENT_HANDLE", "WALLET_ID"}:
            return value.lower()
        return re.sub(r"[ \t]+", " ", value).lower()

    def token(self, ptype: str, value: str) -> str:
        key = (ptype, self._normalize(ptype, value))
        if key not in self._tokens:
            n = self._counters.get(ptype, 0) + 1
            self._counters[ptype] = n
            self._tokens[key] = f"<{ptype}_{n}>"
        token = self._tokens[key]
        self._occurrences[token] = self._occurrences.get(token, 0) + 1
        return token

    def stats(self) -> ScrubStats:
        unique: dict[str, int] = {}
        for token in self._tokens.values():
            ptype = token[1 : token.rindex("_")]
            unique[ptype] = unique.get(ptype, 0) + 1
        return ScrubStats(occurrences=dict(self._occurrences), unique_by_type=unique)


# --- Addresses -------------------------------------------------------------

_ADDRESS = re.compile(
    r"(?im)^(?P<prefix>[ \t]*(?:(?:registered|billing|customer|home|residential|mailing)[ \t]+)?"
    r"address[ \t]*[:#][ \t]*)(?P<value>.+?)[ \t]*$"
)
_ADDRESS_DE = re.compile(
    r"(?im)^(?P<prefix>[ \t]*anschrift[ \t]*[:#][ \t]*)(?P<value>.+?)[ \t]*$"
)

# --- Emails / payment handles ---------------------------------------------

_EMAIL = re.compile(r"(?i)\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b")
_HANDLE = re.compile(r"(?i)(?<![\w.])[A-Z0-9][A-Z0-9._\-]*@[A-Z0-9][A-Z0-9.\-]*")
_AT_HANDLE = re.compile(r"(?i)(?<![\w.])@[A-Z0-9][A-Z0-9._\-]*")

# --- IBAN -----------------------------------------------------------------

_IBAN_LABEL = re.compile(
    r"(?i)(?P<prefix>\bIBAN[ \t]*[:#,]?[ \t]*)"
    r"(?P<value>[A-Z]{2}[ \t]?\d{2}(?:[ \t]?[A-Z0-9]{4}){2,7}(?:[ \t]?[A-Z0-9]{1,4})?)"
    r"(?![A-Z0-9])"
)
_IBAN_PLAIN = re.compile(r"(?i)\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")
_IBAN_SPACED = re.compile(
    r"(?i)\b[A-Z]{2}\d{2}(?:[ \t][A-Z0-9]{4}){2,7}(?:[ \t][A-Z0-9]{1,4})?\b"
)

# Official IBAN lengths per country. Used to stop a labelled IBAN before any
# trailing words on the same line (e.g. "IBAN PK36... Invoice GFP-...").
_IBAN_LENGTHS = {
    "AL": 28, "AD": 24, "AT": 20, "AZ": 28, "BH": 22, "BY": 28, "BE": 16,
    "BA": 20, "BR": 29, "BG": 22, "CR": 22, "HR": 21, "CY": 28, "CZ": 24,
    "DK": 18, "DO": 28, "TL": 23, "EG": 29, "SV": 28, "EE": 20, "FO": 18,
    "FI": 18, "FR": 27, "GE": 22, "DE": 22, "GI": 23, "GR": 27, "GL": 18,
    "GT": 28, "VA": 22, "HU": 28, "IS": 26, "IQ": 23, "IE": 22, "IL": 23,
    "IT": 27, "JO": 30, "KZ": 20, "XK": 20, "KW": 30, "LV": 21, "LB": 28,
    "LY": 25, "LI": 21, "LT": 20, "LU": 20, "MK": 19, "MT": 31, "MR": 27,
    "MU": 30, "MD": 24, "MC": 27, "MN": 20, "ME": 22, "NL": 18, "NO": 15,
    "PK": 24, "PS": 29, "PL": 28, "PT": 25, "QA": 29, "RO": 24, "LC": 32,
    "SM": 27, "ST": 25, "SA": 24, "RS": 22, "SC": 31, "SK": 24, "SI": 19,
    "ES": 24, "SD": 18, "SE": 24, "CH": 21, "TN": 24, "TR": 26, "UA": 29,
    "AE": 23, "GB": 22,
}

# --- Cards ----------------------------------------------------------------

_MASKED_CARD = re.compile(r"\b\d{4,6}[ \-]?(?:\*{2,}|[xX]{4,})[ \-]?\d{4}\b")
_CARD_NUMBER = re.compile(r"(?<![\w.])(?:\d[ \-]?){12,18}\d(?![\w.])")

# --- National IDs ---------------------------------------------------------

_CNIC_LABEL = re.compile(
    r"(?i)(?P<prefix>\bCNIC(?:[ \t]*(?:No\.?|Number))?[ \t]*[:#,]?[ \t]*)"
    r"(?P<value>\d{5}[ \-]?\d{7}[ \-]?\d)"
)
_CNIC_GENERIC = re.compile(r"\b\d{5}-\d{7}-\d\b")
_SSN_LABEL = re.compile(
    r"(?i)(?P<prefix>\bSSN(?:[ \t]*(?:on[ \t]*file|No\.?|Number))?[ \t]*[:#,]?[ \t]*)"
    r"(?P<value>\d{3}[ \-]?\d{2}[ \-]?\d{4})"
)
_SSN_GENERIC = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
_SIN_LABEL = re.compile(
    r"(?i)(?P<prefix>\bSIN[ \t]*[:#,]?[ \t]*)(?P<value>\d{3}[ \-]?\d{3}[ \-]?\d{3})"
)
_NI_LABEL = re.compile(
    r"(?i)(?P<prefix>\bNI(?:[ \t]*(?:Number|No\.?))?[ \t]*[:#,]?[ \t]*)"
    r"(?P<value>[A-CEGHJ-PR-TW-Z]{2}[ \t]?\d{2}[ \t]?\d{2}[ \t]?\d{2}[ \t]?[A-D])"
)
_NI_GENERIC = re.compile(r"\b[A-CEGHJ-PR-TW-Z]{2}[ \t]?\d{2}[ \t]?\d{2}[ \t]?\d{2}[ \t]?[A-D]\b")
_PAN_LABEL = re.compile(
    r"(?i)(?P<prefix>\bPAN[ \t]*[:#,]?[ \t]*)(?P<value>[A-Z]{5}\d{4}[A-Z])"
)
_PAN_GENERIC = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
_AADHAAR_LABEL = re.compile(
    r"(?i)(?P<prefix>\bAadhaar(?:[ \t]*(?:Number|No\.?))?[ \t]*[:#,]?[ \t]*)"
    r"(?P<value>\d{4}[ \-]?\d{4}[ \-]?\d{4})"
)
_AADHAAR_GENERIC = re.compile(
    r"(?<![\d \-])\b\d{4}[ \t]\d{4}[ \t]\d{4}\b(?![\s\-]\d{4})"
)
_STEUER_LABEL = re.compile(
    r"(?i)(?P<prefix>\bSteuer-?ID[ \t]*[:#,]?[ \t]*)"
    r"(?P<value>\d{2}[ \t]?\d{3}[ \t]?\d{3}[ \t]?\d{3})"
)

# --- Bank routing ---------------------------------------------------------

_BIC_LABEL = re.compile(
    r"(?i)(?P<prefix>\b(?:BIC|SWIFT(?:[ \t]*Code)?)[ \t]*[:#,]?[ \t]*)"
    r"(?P<value>[A-Z]{4}[A-Z]{2}[A-Z0-9]{2}(?:[A-Z0-9]{3})?)"
)
_BIC_GENERIC = re.compile(
    r"(?<![A-Z0-9])([A-Z]{4})([A-Z]{2})([A-Z0-9]{2})(?:[A-Z0-9]{3})?(?![A-Z0-9])"
)
_SORT_LABEL = re.compile(
    r"(?i)(?P<prefix>\bSort[ \t]*Code[ \t]*[:#,]?[ \t]*)"
    r"(?P<value>\d{2}[ \-]?\d{2}[ \-]?\d{2}(?:[ \t]*\(\d{6}\))?)"
)
_ROUTING_LABEL = re.compile(
    r"(?i)(?P<prefix>\bRouting(?:[ \t]*(?:Number|No\.?))?[ \t]*[:#,]?[ \t]*)"
    r"(?P<value>\d{9})"
)
_IFSC_LABEL = re.compile(
    r"(?i)(?P<prefix>\bIFSC[ \t]*[:#,]?[ \t]*)(?P<value>[A-Z]{4}0[A-Z0-9]{6})"
)
_IFSC_GENERIC = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")
_MICR_LABEL = re.compile(
    r"(?i)(?P<prefix>\bMICR[ \t]*[:#,]?[ \t]*)(?P<value>\d{9})"
)
_TRANSIT_LABEL = re.compile(
    r"(?i)(?P<prefix>\bTransit[ \t]*[:#,]?[ \t]*)(?P<value>\d{5})"
)
_INSTITUTION_LABEL = re.compile(
    r"(?i)(?P<prefix>\bInstitution[ \t]*[:#,]?[ \t]*)(?P<value>\d{3})"
)
_BLZ_LABEL = re.compile(
    r"(?i)(?P<prefix>\b(?:BLZ|Bankleitzahl)[ \t]*[:#,]?[ \t]*)(?P<value>\d{8})"
)
_CREDITOR_ID_LABEL = re.compile(
    r"(?i)(?P<prefix>\b(?:Glaeubiger-?ID|Creditor[ \t]*ID)[ \t]*[:#,]?[ \t]*)"
    r"(?P<value>[A-Z]{2}\d{2}[A-Z0-9]{5,30})"
)

# --- Account numbers ------------------------------------------------------

_ACCOUNT_LABEL = re.compile(
    r"(?i)(?P<prefix>\b(?:A/C[ \t]*(?:No\.?)?|Account[ \t]*(?:Number|No\.?|#)|"
    r"Acc(?:ount)?|Kontonummer|Consumer[ \t]*(?:Number|No\.?)|ACCT)[ \t]*[:#,]?[ \t]*)"
    r"(?P<value>\d[\d \t\-]{5,})"
)
_GROUPED_ACCOUNT = re.compile(r"(?<![\w.\-])\d{4}(?:[-\s]\d{4}){2,3}(?![\w.\-])")

# --- Wallet IDs -----------------------------------------------------------

_WALLET_ID_LABEL = re.compile(
    r"(?i)(?P<prefix>\bWallet[ \t]*ID[ \t]*[:#,]?[ \t]*)"
    r"(?P<value>[A-Z0-9][A-Z0-9._\-]{2,})"
)

# --- Phones ---------------------------------------------------------------

_PHONE_LABEL = re.compile(
    r"(?i)(?P<prefix>\b(?:Registered[ \t]+Phone|Phone|Telephone|Tel|Cell|"
    r"Mobile|Mob(?:ile)?|Handynummer)[ \t]*[:#][ \t]*)(?P<value>[^\n]+?)"
)
_PHONE_INTL = re.compile(
    r"(?<![\w.])\+\d{1,3}[ .\-]?(?:\(\d{1,4}\)[ .\-]?)?\d(?:[\d .\-()]{5,}\d)(?![\w.])"
)
_PHONE_LOCAL = re.compile(
    r"(?<![\w.])(?:\(\d{2,4}\)[ .\-]?)?0\d{2,4}[ .\-]\d{3,4}[ .\-]?\d{3,4}(?![\w.])"
)
_PHONE_PAREN = re.compile(
    r"(?<![\w.])\(\d{2,4}\)[ .\-]?\d{3,4}[ .\-]?\d{3,4}(?![\w.])"
)
_PHONE_NA = re.compile(r"(?<![\w.])\d{3}[ .\-]\d{3}[ .\-]\d{4}(?![\w.])")

# --- Reference / trace / transaction IDs ----------------------------------

_TXN_IDS_LINE = re.compile(
    r"(?im)^(?P<prefix>[ \t]*Transaction[ \t]*IDs?[ \t]*[:#][ \t]*)(?P<value>.+?)[ \t]*$"
)
_REF_LABEL = re.compile(
    r"(?i)(?P<prefix>\b(?:Customer[ \t]*Support[ \t]*Reference|MANDATSREF|"
    r"Image[ \t]*Ref|Transaction[ \t]*ID|Trans[ \t]*ID|Reference|Trace|UTR|RRN|"
    r"Order(?:[ \t]*No\.?)?|Invoice(?:[ \t]*No\.?)?|Cheque[ \t]*(?:No\.?)?|"
    r"Warrant(?:[ \t]*No\.?)?|Ref)[ \t]*[:#,]?[ \t]*)"
    r"(?P<value>[A-Z0-9][A-Z0-9./\-]{2,})"
)

# --- IP -------------------------------------------------------------------

_IP_LABEL = re.compile(
    r"(?i)(?P<prefix>\b(?:(?:Login[ \t]+)?IP(?:[ \t]*\([^)]*\))?)[ \t]*[:#]?[ \t]*)"
    r"(?P<value>\d{1,3}(?:\.\d{1,3}){3})"
)

# --- Generic fallbacks ----------------------------------------------------

_LONG_DIGITS = re.compile(r"(?<![\w.,])\d{10,}(?![\w.,])")
_LONG_ALNUM = re.compile(
    r"(?<![A-Z0-9])(?=[A-Z0-9./\-]*\d)(?=[A-Z0-9./\-]*[A-Z])"
    r"[A-Z0-9][A-Z0-9./\-]{9,}(?![A-Z0-9])"
)
_MASKED_LAST4 = re.compile(r"(?i)[x*]{2,}\d{4}")
_DATE_LIKE = (
    re.compile(r"(?i)\d{4}-[a-z]{3}-\d{2}"),
    re.compile(r"(?i)\d{2}-[a-z]{3}-\d{4}"),
    re.compile(r"\d{4}/\d{2}/\d{2}"),
)


def _sub_prefix(pattern: re.Pattern[str], ptype: str, text: str, vault: PlaceholderVault, guard=None) -> str:
    def repl(match: re.Match[str]) -> str:
        value = match.group("value")
        if not value or (guard is not None and not guard(value)):
            return match.group(0)
        return match.group("prefix") + vault.token(ptype, value)

    return pattern.sub(repl, text)


def _sub_whole(pattern: re.Pattern[str], ptype: str, text: str, vault: PlaceholderVault, guard=None) -> str:
    def repl(match: re.Match[str]) -> str:
        value = match.group(0)
        if guard is not None and not guard(value):
            return value
        return vault.token(ptype, value)

    return pattern.sub(repl, text)


def _valid_iban(value: str) -> bool:
    compact = re.sub(r"[ \t]", "", value).upper()
    if not 15 <= len(compact) <= 34:
        return False
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]+", compact):
        return False
    rearranged = compact[4:] + compact[:4]
    numeric = "".join(str(int(ch, 36)) for ch in rearranged)
    return int(numeric) % 97 == 1


def _luhn(value: str) -> bool:
    digits = [int(ch) for ch in value if ch.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    total = 0
    for index, digit in enumerate(reversed(digits)):
        if index % 2 == 1:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def _has_digits(value: str, minimum: int) -> bool:
    return sum(ch.isdigit() for ch in value) >= minimum


def _scrub_addresses(text: str, vault: PlaceholderVault) -> str:
    text = _sub_prefix(_ADDRESS, "ADDRESS", text, vault, guard=lambda v: len(v.strip()) > 3)
    return _sub_prefix(_ADDRESS_DE, "ADDRESS", text, vault, guard=lambda v: len(v.strip()) > 3)


def _scrub_emails(text: str, vault: PlaceholderVault) -> str:
    def repl(match: re.Match[str]) -> str:
        value = match.group(0)
        domain = value.rsplit("@", 1)[-1].lower()
        base = domain.split(".")[0]
        ptype = "PAYMENT_HANDLE" if base in _WALLET_DOMAINS or domain in _WALLET_DOMAINS else "EMAIL"
        return vault.token(ptype, value)

    text = _EMAIL.sub(repl, text)
    text = _sub_whole(_HANDLE, "PAYMENT_HANDLE", text, vault)
    return _sub_whole(_AT_HANDLE, "PAYMENT_HANDLE", text, vault)


def _iban_cut(value: str) -> int:
    """Return how many non-space characters of *value* belong to the IBAN."""
    compact = re.sub(r"[ \t]", "", value)
    if len(compact) < 15:
        return 0

    expected = _IBAN_LENGTHS.get(compact[:2].upper())
    if expected and len(compact) >= expected:
        return expected

    mode: str | None = None
    count = 0
    index = 0
    length = len(value)
    while index < length and count < 34:
        char = value[index]
        if char in " \t":
            start = index + 1
            while start < length and value[start] in " \t":
                start += 1
            end = start
            while end < length and value[end] not in " \t":
                end += 1
            token = value[start:end]
            letters = [c for c in token if c.isalpha()]
            if letters:
                token_mode = (
                    "lower"
                    if all(c.islower() for c in letters)
                    else "upper"
                    if all(c.isupper() for c in letters)
                    else "mixed"
                )
                if mode is None:
                    mode = token_mode
                if token_mode == "mixed" or token_mode != mode:
                    break
            if len(token) > 4:
                break
            index = start
            continue
        count += 1
        index += 1
    return count


def _split_iban(value: str) -> tuple[str, str]:
    take = _iban_cut(value)
    if take < 15:
        return "", value
    seen = 0
    end = 0
    for index, char in enumerate(value):
        if char not in " \t":
            seen += 1
            if seen == take:
                end = index + 1
                break
    if end == 0:
        end = len(value)
    return value[:end], value[end:]


def _scrub_ibans(text: str, vault: PlaceholderVault) -> str:
    def repl_label(match: re.Match[str]) -> str:
        candidate, rest = _split_iban(match.group("value"))
        if len(re.sub(r"[ \t]", "", candidate)) < 15:
            return match.group(0)
        return match.group("prefix") + vault.token("IBAN", candidate) + rest

    text = _IBAN_LABEL.sub(repl_label, text)

    def repl_plain(match: re.Match[str]) -> str:
        value = match.group(0)
        candidate, rest = _split_iban(value)
        if not _valid_iban(candidate):
            return value
        return vault.token("IBAN", candidate) + rest

    text = _IBAN_PLAIN.sub(repl_plain, text)
    return _IBAN_SPACED.sub(repl_plain, text)


def _scrub_cards(text: str, vault: PlaceholderVault) -> str:
    text = _sub_whole(_MASKED_CARD, "CARD", text, vault)
    return _sub_whole(_CARD_NUMBER, "CARD", text, vault, guard=_luhn)


def _scrub_national_ids(text: str, vault: PlaceholderVault) -> str:
    text = _sub_prefix(_CNIC_LABEL, "CNIC", text, vault)
    text = _sub_whole(_CNIC_GENERIC, "CNIC", text, vault)
    text = _sub_prefix(_SSN_LABEL, "SSN", text, vault)
    text = _sub_whole(_SSN_GENERIC, "SSN", text, vault)
    text = _sub_prefix(_SIN_LABEL, "SIN", text, vault)
    text = _sub_prefix(_NI_LABEL, "NI", text, vault)
    text = _sub_whole(_NI_GENERIC, "NI", text, vault)
    text = _sub_prefix(_PAN_LABEL, "PAN", text, vault)
    text = _sub_whole(_PAN_GENERIC, "PAN", text, vault)
    text = _sub_prefix(_AADHAAR_LABEL, "AADHAAR", text, vault)
    text = _sub_whole(_AADHAAR_GENERIC, "AADHAAR", text, vault)
    return _sub_prefix(_STEUER_LABEL, "TAX_ID", text, vault)


def _scrub_routing(text: str, vault: PlaceholderVault) -> str:
    text = _sub_prefix(_BIC_LABEL, "BIC", text, vault)
    text = _sub_whole(_BIC_GENERIC, "BIC", text, vault, guard=lambda v: v[4:6] in _BIC_COUNTRIES)
    text = _sub_prefix(_SORT_LABEL, "SORT_CODE", text, vault)
    text = _sub_prefix(_ROUTING_LABEL, "ROUTING", text, vault)
    text = _sub_prefix(_IFSC_LABEL, "IFSC", text, vault)
    text = _sub_whole(_IFSC_GENERIC, "IFSC", text, vault)
    text = _sub_prefix(_MICR_LABEL, "MICR", text, vault)
    text = _sub_prefix(_TRANSIT_LABEL, "TRANSIT", text, vault)
    text = _sub_prefix(_INSTITUTION_LABEL, "INSTITUTION", text, vault)
    text = _sub_prefix(_BLZ_LABEL, "BLZ", text, vault)
    return _sub_prefix(_CREDITOR_ID_LABEL, "ROUTING", text, vault)


def _scrub_accounts(text: str, vault: PlaceholderVault) -> str:
    text = _sub_prefix(_ACCOUNT_LABEL, "ACCOUNT_ID", text, vault)
    return _sub_whole(_GROUPED_ACCOUNT, "ACCOUNT_ID", text, vault)


def _scrub_wallet_ids(text: str, vault: PlaceholderVault) -> str:
    return _sub_prefix(_WALLET_ID_LABEL, "WALLET_ID", text, vault)


def _scrub_phones(text: str, vault: PlaceholderVault) -> str:
    text = _sub_prefix(_PHONE_LABEL, "PHONE", text, vault, guard=lambda v: _has_digits(v, 7))
    text = _sub_whole(_PHONE_INTL, "PHONE", text, vault, guard=lambda v: 7 <= sum(c.isdigit() for c in v) <= 16)
    text = _sub_whole(_PHONE_LOCAL, "PHONE", text, vault, guard=lambda v: _has_digits(v, 9))
    text = _sub_whole(_PHONE_PAREN, "PHONE", text, vault, guard=lambda v: _has_digits(v, 7))
    return _sub_whole(_PHONE_NA, "PHONE", text, vault, guard=lambda v: _has_digits(v, 10))


def _scrub_references(text: str, vault: PlaceholderVault) -> str:
    text = _sub_prefix(_TXN_IDS_LINE, "REF", text, vault, guard=lambda v: len(v.strip()) > 2)
    return _sub_prefix(_REF_LABEL, "REF", text, vault)


def _scrub_ips(text: str, vault: PlaceholderVault) -> str:
    def guard(value: str) -> bool:
        return all(0 <= int(part) <= 255 for part in value.split("."))

    return _sub_prefix(_IP_LABEL, "IP", text, vault, guard=guard)


def _alnum_guard(value: str) -> bool:
    if value.startswith("<"):
        return False
    if _MASKED_LAST4.fullmatch(value):
        return False
    if any(pattern.fullmatch(value) for pattern in _DATE_LIKE):
        return False
    return _has_digits(value, 4)


def _scrub_generic_references(text: str, vault: PlaceholderVault) -> str:
    text = _sub_whole(_LONG_DIGITS, "REF", text, vault)
    return _sub_whole(_LONG_ALNUM, "REF", text, vault, guard=_alnum_guard)


def scrub_text(text: str, vault: PlaceholderVault | None = None) -> str:
    """Scrub one block of text locally, returning the same text with placeholders."""
    if not text:
        return text
    vault = vault or PlaceholderVault()

    text = _scrub_addresses(text, vault)
    text = _scrub_emails(text, vault)
    text = _scrub_ibans(text, vault)
    text = _scrub_national_ids(text, vault)
    text = _scrub_routing(text, vault)
    text = _scrub_references(text, vault)
    text = _scrub_cards(text, vault)
    text = _scrub_accounts(text, vault)
    text = _scrub_wallet_ids(text, vault)
    text = _scrub_phones(text, vault)
    text = _scrub_ips(text, vault)
    return _scrub_generic_references(text, vault)
