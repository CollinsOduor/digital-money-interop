
def format_amount(amount: float) -> str:
    """Helper function to format Kenyan Shillings"""
    return f"Ksh {amount:,.2f}"


def normalize_msisdn(phone_number: str) -> str:
    digits = ''.join(ch for ch in phone_number if ch.isdigit())
    if digits.startswith('0'):
        digits = f"254{digits[1:]}"
    elif digits.startswith('7') and len(digits) == 9:
        digits = f"254{digits}"
    if len(digits) != 12 or not digits.startswith('254'):
        raise ValueError("Phone number must be Kenyan e.g. 07XXXXXXXX or 2547XXXXXXXX")
    return digits