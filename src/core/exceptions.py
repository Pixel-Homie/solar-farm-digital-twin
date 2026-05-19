class SolarTwinError(Exception):
    """Base exception for the application."""
    pass

class NetworkError(SolarTwinError):
    pass

class TimeoutError(NetworkError):
    pass

class HTTPError(NetworkError):
    pass

class ParseError(SolarTwinError):
    pass

class CoverageError(SolarTwinError):
    pass

class ConfigurationError(SolarTwinError):
    pass
