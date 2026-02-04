"""IM Platform Adapters module."""

from .base import BaseIMAdapter, IncomingMessage, OutgoingMessage, User, Channel
from .factory import IMManager, create_adapter
