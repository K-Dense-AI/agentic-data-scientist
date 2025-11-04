"""
Event data models for Agentic Data Scientist streaming responses.

Provides structured definitions for all event types used in the streaming interface.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional


@dataclass
class BaseEvent:
    """Base class for all streaming events."""

    type: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S.%f")[:-3])


@dataclass
class MessageEvent(BaseEvent):
    """Agent message event containing text content."""

    type: Literal["message"] = "message"
    content: str = ""
    author: str = "agent"
    is_thought: bool = False
    is_partial: bool = False
    event_number: Optional[int] = None


@dataclass
class FunctionCallEvent(BaseEvent):
    """Function/tool call event from an agent."""

    type: Literal["function_call"] = "function_call"
    name: str = ""
    arguments: Dict[str, Any] = field(default_factory=dict)
    author: str = "agent"
    event_number: Optional[int] = None


@dataclass
class FunctionResponseEvent(BaseEvent):
    """Function/tool response event."""

    type: Literal["function_response"] = "function_response"
    name: str = ""
    response: Any = None
    author: str = "agent"
    event_number: Optional[int] = None


@dataclass
class FileCreatedEvent(BaseEvent):
    """File creation notification event."""

    type: Literal["file_created"] = "file_created"
    file_path: str = ""
    file_size: int = 0
    event_number: Optional[int] = None


@dataclass
class UsageEvent(BaseEvent):
    """Token usage metadata event."""

    type: Literal["usage"] = "usage"
    usage: Dict[str, int] = field(
        default_factory=lambda: {"total_input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}
    )


@dataclass
class KeepaliveEvent(BaseEvent):
    """Keepalive event to prevent connection timeout."""

    type: Literal["keepalive"] = "keepalive"
    content: str = "Still processing..."
    event_number: Optional[int] = None


@dataclass
class ErrorEvent(BaseEvent):
    """Error event with error details."""

    type: Literal["error"] = "error"
    content: str = ""


@dataclass
class CompletedEvent(BaseEvent):
    """Session completion event with summary information."""

    type: Literal["completed"] = "completed"
    session_id: str = ""
    duration: float = 0.0
    total_events: int = 0
    files_created: List[str] = field(default_factory=list)
    files_count: int = 0


# Type union for all event types
StreamingEvent = (
    MessageEvent
    | FunctionCallEvent
    | FunctionResponseEvent
    | FileCreatedEvent
    | UsageEvent
    | KeepaliveEvent
    | ErrorEvent
    | CompletedEvent
)


# Event type mapping for easy construction
EVENT_TYPE_MAP = {
    "message": MessageEvent,
    "function_call": FunctionCallEvent,
    "function_response": FunctionResponseEvent,
    "file_created": FileCreatedEvent,
    "usage": UsageEvent,
    "keepalive": KeepaliveEvent,
    "error": ErrorEvent,
    "completed": CompletedEvent,
}


def create_event(event_type: str, **kwargs) -> StreamingEvent:
    """
    Factory function to create appropriate event based on type.

    Parameters
    ----------
    event_type : str
        The type of event to create
    **kwargs
        Event-specific fields

    Returns
    -------
    StreamingEvent
        Appropriate event instance

    Raises
    ------
    ValueError
        If event_type is not recognized
    """
    event_class = EVENT_TYPE_MAP.get(event_type)
    if not event_class:
        raise ValueError(f"Unknown event type: {event_type}")

    # Filter kwargs to only include valid fields for the event class
    valid_fields = {f.name for f in event_class.__dataclass_fields__.values()}
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_fields}

    return event_class(**filtered_kwargs)


def event_to_dict(event: StreamingEvent) -> Dict[str, Any]:
    """
    Convert an event to a dictionary for JSON serialization.

    Parameters
    ----------
    event : StreamingEvent
        The event to convert

    Returns
    -------
    Dict[str, Any]
        Dictionary representation of the event
    """
    result = {"type": event.type}

    # Add all non-None fields
    for field_name in event.__dataclass_fields__:
        value = getattr(event, field_name)
        if value is not None and field_name != "type":
            result[field_name] = value

    return result
