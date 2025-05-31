"""
Custom exceptions for Vector Database MCP Server
"""


class VectorDatabaseError(Exception):
    """Base exception for vector database errors"""
    pass


class SessionError(VectorDatabaseError):
    """Exception for session-related errors"""
    pass


class DocumentError(VectorDatabaseError):
    """Exception for document-related errors"""
    pass


class ValidationError(VectorDatabaseError):
    """Exception for validation errors"""
    pass


class EntropyError(VectorDatabaseError):
    """Exception for entropy generation errors"""
    pass


class OscillationError(VectorDatabaseError):
    """Exception for oscillation calculation errors"""
    pass


class DatabaseConnectionError(VectorDatabaseError):
    """Exception for database connection errors"""
    pass


class CharacterNotFoundError(VectorDatabaseError):
    """Exception when character is not found"""
    pass


class SessionNotFoundError(SessionError):
    """Exception when session is not found"""
    pass


class InvalidSessionError(SessionError):
    """Exception for invalid session operations"""
    pass


class DocumentNotFoundError(DocumentError):
    """Exception when document is not found"""
    pass


class DocumentAccessError(DocumentError):
    """Exception for document access errors"""
    pass


class SecurityError(VectorDatabaseError):
    """Exception for security-related errors"""
    pass


class PathTraversalError(SecurityError):
    """Exception for path traversal attempts"""
    pass
