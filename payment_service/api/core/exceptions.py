class PayUError(Exception):
    """Basic communication error with PayU."""
    pass

class TokenError(PayUError):
    """Token acquisition error."""
    pass

class OrderError(PayUError):
    """Error in order related operation."""
    pass
