"""
Event compression system using LLM-based summarization.

This module provides callback-based event compression that triggers when
the event count exceeds a threshold. It uses LLM summarization to create
concise summaries of event sequences.
"""

import logging
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.events import Event, EventActions
from google.adk.events.event_actions import EventCompaction
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.llm_request import LlmRequest
from google.genai import types as genai_types

from agentic_data_scientist.agents.adk.utils import DEFAULT_MODEL_NAME, OPENROUTER_API_BASE, OPENROUTER_API_KEY


logger = logging.getLogger(__name__)

# Default compression settings
DEFAULT_EVENT_THRESHOLD = 40  # Compress when this many events accumulate (more aggressive)
DEFAULT_OVERLAP_SIZE = 20  # Keep this many recent events uncompressed (smaller window)
LARGE_TEXT_THRESHOLD = 10000  # Truncate texts larger than this (more aggressive)
LARGE_TEXT_KEEP = 1000  # Keep only this many chars from large texts


def _truncate_large_event_texts(events: list[Event]) -> None:
    """
    Truncate large text content in events (in-place modification).

    This preprocessing step reduces token count by truncating any text
    part larger than LARGE_TEXT_THRESHOLD to LARGE_TEXT_KEEP characters.

    Parameters
    ----------
    events : list[Event]
        Events to preprocess (modified in-place)
    """
    truncated_count = 0

    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    text_len = len(part.text)
                    if text_len > LARGE_TEXT_THRESHOLD:
                        # Truncate text to first 1k chars
                        part.text = (
                            part.text[:LARGE_TEXT_KEEP] + f"\n\n[... truncated {text_len - LARGE_TEXT_KEEP} chars ...]"
                        )
                        truncated_count += 1

    if truncated_count > 0:
        logger.info(f"[Compression] Truncated {truncated_count} large text parts (>{LARGE_TEXT_THRESHOLD} chars)")


async def _create_event_summary_with_llm(
    events: list[Event],
    model_name: str,
    session_service,
    session,
) -> str:
    """
    Generate a concise summary of events using LLM.

    Parameters
    ----------
    events : list[Event]
        Events to summarize
    model_name : str
        Model name string to use for summarization
    session_service : SessionService
        Session service for accessing sessions
    session : Session
        Current session

    Returns
    -------
    str
        Concise summary of events
    """
    # Format events for LLM summarization
    event_descriptions = []
    events_with_text = 0
    events_with_tools = 0
    total_text_chars = 0

    for i, event in enumerate(events):
        author = event.author or "unknown"

        # Extract key content
        content_texts = []
        tool_calls = []
        function_responses = []

        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    # Keep more text for better summarization (500 chars instead of 200)
                    text = part.text[:500] if len(part.text) > 500 else part.text
                    content_texts.append(text)
                    total_text_chars += len(part.text)
                    events_with_text += 1
                if hasattr(part, 'function_call') and part.function_call:
                    tool_calls.append(part.function_call.name)
                    events_with_tools += 1
                if hasattr(part, 'function_response') and part.function_response:
                    # Extract function response name
                    if hasattr(part.function_response, 'name'):
                        function_responses.append(part.function_response.name)

        # Format event description - be more detailed
        desc_parts = [f"Event {i} [{author}]"]
        if tool_calls:
            desc_parts.append(f"Tools: {', '.join(tool_calls)}")
        if function_responses:
            desc_parts.append(f"Responses: {', '.join(function_responses)}")
        if content_texts:
            # Include the actual content text
            desc_parts.append(f"Content: {' | '.join(content_texts)}")

        desc = " - ".join(desc_parts)
        event_descriptions.append(desc)

    # Log statistics about events being summarized
    logger.info(
        f"[Compression] Event breakdown: {events_with_text} with text, "
        f"{events_with_tools} with tools, total {total_text_chars} chars"
    )

    # Create summarization prompt
    events_text = "\n".join(event_descriptions[:100])  # Limit to first 100 events

    prompt = f"""You are summarizing a sequence of {len(events)} agent events for context compression.

Events to summarize:
{events_text}

Provide a comprehensive summary (aim for 400-600 words) that covers:
1. Event count and time period
2. Key agents involved and their roles
3. Major actions taken (tool calls, file operations, commands run)
4. Important outcomes, results, and data discovered
5. Files created or modified
6. Any errors or issues encountered
7. Current state and what comes next

Be detailed and specific - this summary replaces the original events, so preserve critical information that downstream agents will need."""

    # Call LLM for summarization
    try:
        # Create LiteLlm instance with the model NAME (string, not object!)
        llm = LiteLlm(
            model=model_name,
            num_retries=3,
            timeout=30,
            api_base=OPENROUTER_API_BASE if OPENROUTER_API_KEY else None,
            custom_llm_provider="openrouter" if OPENROUTER_API_KEY else None,
        )

        # Create LlmRequest with proper structure
        llm_request = LlmRequest(
            model=model_name,
            contents=[genai_types.Content(role="user", parts=[genai_types.Part(text=prompt)])],
            config=genai_types.GenerateContentConfig(
                temperature=0.3, max_output_tokens=4000
            ),  # Increased for more detailed summaries
        )

        # Call LLM
        response = None
        async for llm_response in llm.generate_content_async(llm_request=llm_request, stream=False):
            response = llm_response
            break  # Only need first (and only) response

        # Extract summary text from LlmResponse
        if response and response.content and response.content.parts:
            parts = response.content.parts
            if len(parts) > 0 and parts[0].text:
                summary = parts[0].text
                logger.info(
                    f"[Compression] ✓ LLM generated summary ({len(summary)} chars, ~{len(summary) // 4} tokens)"
                )
                # Log first 200 chars of summary for inspection
                logger.info(f"[Compression] Summary preview: {summary[:200]}")
                return summary

        # Fallback summary if LLM fails to return content
        logger.warning("[Compression] LLM returned empty response")
        return f"[COMPRESSED] {len(events)} events with agents: {', '.join(set(e.author for e in events if e.author))}"

    except Exception as e:
        logger.warning(f"[Compression] LLM summarization failed: {e}", exc_info=True)
        # Fallback summary
        return f"[COMPRESSED] {len(events)} events from multiple agents. LLM summarization unavailable."


async def _compress_session_events(
    session,
    start_idx: int,
    end_idx: int,
    summary_text: str,
    session_service,
):
    """
    Apply compression by creating a summary event and removing old events.

    Parameters
    ----------
    session : Session
        Session to compress
    start_idx : int
        Start index of events to compress
    end_idx : int
        End index of events to compress (exclusive)
    summary_text : str
        Summary text from LLM
    session_service : SessionService
        Session service for event operations
    """
    events = session.events

    if start_idx >= end_idx or end_idx > len(events):
        logger.warning(f"[Compression] Invalid compression range: {start_idx}:{end_idx} (total {len(events)})")
        return

    # Get timestamp range
    start_timestamp = events[start_idx].timestamp if start_idx < len(events) else 0.0
    end_timestamp = events[end_idx - 1].timestamp if end_idx <= len(events) else 0.0

    # Create compaction event
    compaction = EventCompaction(
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        compacted_content=genai_types.Content(role='model', parts=[genai_types.Part(text=summary_text)]),
    )

    # Create summary event with compaction action
    summary_event = Event(
        author='event_compression',
        actions=EventActions(compaction=compaction),
        invocation_id=events[0].invocation_id if events else None,
    )

    # CRITICAL FIX: Build new event list with direct assignment
    # Keep events before compression range, add summary, keep events after
    new_events = events[:start_idx] + [summary_event] + events[end_idx:]

    # ADDITIONAL FIX: Aggressively truncate remaining events to prevent token overflow
    # This ensures ALL events in the session stay within reasonable size
    logger.info(f"[Compression] Truncating remaining {len(new_events)} events for safety")
    _truncate_large_event_texts(new_events)

    # Direct assignment to session.events (like working example)
    session.events = new_events

    events_removed = end_idx - start_idx

    # Calculate approximate token reduction
    summary_tokens_approx = len(summary_text) // 4  # Rough estimate: 1 token ≈ 4 chars

    # Calculate total tokens in remaining events
    total_chars = 0
    for evt in session.events:
        if evt.content and evt.content.parts:
            for part in evt.content.parts:
                if hasattr(part, 'text') and part.text:
                    total_chars += len(part.text)

    logger.warning(
        f"[Compression] ✓ Compressed {events_removed} events (idx {start_idx}:{end_idx}) "
        f"into 1 summary event (~{summary_tokens_approx} tokens). "
        f"Total events: {len(session.events)} (was {len(events)}), ~{total_chars // 4} tokens remaining"
    )


def create_compression_callback(
    event_threshold: int = DEFAULT_EVENT_THRESHOLD,
    overlap_size: int = DEFAULT_OVERLAP_SIZE,
    model_name: Optional[str] = None,
):
    """
    Factory function to create an event compression callback.

    The callback can be used as an after_agent_callback in ADK agents.
    It triggers compression when the event count exceeds the threshold.

    Parameters
    ----------
    event_threshold : int, optional
        Number of events that triggers compression (default: 40)
    overlap_size : int, optional
        Number of recent events to keep uncompressed (default: 20)
    model_name : str, optional
        Model name string for summarization (default: DEFAULT_MODEL_NAME)

    Returns
    -------
    Callable
        Async callback function compatible with after_agent_callback

    Examples
    --------
    >>> callback = create_compression_callback(event_threshold=40, overlap_size=20)
    >>> agent = LlmAgent(
    ...     name="my_agent",
    ...     instruction="...",
    ...     after_agent_callback=callback,
    ... )
    """
    if model_name is None:
        model_name = DEFAULT_MODEL_NAME

    async def compression_callback(callback_context: CallbackContext):
        """
        After-agent callback that compresses events when threshold is exceeded.

        Parameters
        ----------
        callback_context : CallbackContext
            Callback context with invocation context access

        Returns
        -------
        None
            Returns None to allow normal event flow
        """
        ctx = callback_context._invocation_context
        session = ctx.session
        events = session.events

        event_count = len(events)

        # Calculate approximate token count in events for debugging
        total_chars = 0
        event_sizes = []
        authors_count = {}
        events_with_content = 0

        for i, event in enumerate(events):
            event_chars = 0
            has_content = False

            # Track authors
            author = event.author or "unknown"
            authors_count[author] = authors_count.get(author, 0) + 1

            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        event_chars += len(part.text)
                        has_content = True
                    # Also check for function calls/responses
                    if hasattr(part, 'function_call'):
                        has_content = True
                    if hasattr(part, 'function_response'):
                        has_content = True

            if has_content:
                events_with_content += 1

            total_chars += event_chars
            if event_chars > 10000:  # Log large events
                event_sizes.append(f"Event {i} [{event.author}]: {event_chars} chars")

        approx_tokens = total_chars // 4  # Rough estimate

        # Log event count and token estimate for debugging
        logger.warning(
            f"[Compression] Callback triggered: {event_count} events, ~{approx_tokens} tokens "
            f"(~{total_chars} chars), threshold: {event_threshold}"
        )
        logger.warning(
            f"[Compression] Events with actual content: {events_with_content}/{event_count} "
            f"Authors: {dict(list(authors_count.items())[:5])}"
        )

        # Log large events
        if event_sizes:
            logger.warning(f"[Compression] Large events detected: {len(event_sizes)}")
            for size_info in event_sizes[:5]:  # Show first 5 large events
                logger.warning(f"[Compression]   {size_info}")

        # Check if compression is needed
        if event_count <= event_threshold:
            logger.debug(f"[Compression] Event count {event_count} below threshold {event_threshold}, skipping")
            return None

        logger.warning(f"[Compression] ⚠️ Event count {event_count} exceeds threshold {event_threshold}, compressing...")

        # Determine compression range
        # Compress from 0 to (total - overlap_size)
        end_idx = event_count - overlap_size

        if end_idx <= 0:
            logger.warning(f"[Compression] Not enough events to compress (need > {overlap_size})")
            return None

        # Find last compaction to avoid re-compressing
        last_compaction_idx = -1
        for i in range(len(events) - 1, -1, -1):
            if events[i].actions and events[i].actions.compaction:
                last_compaction_idx = i
                break

        # Start compression from after last compaction
        start_idx = max(0, last_compaction_idx + 1)

        if start_idx >= end_idx:
            logger.debug(f"[Compression] No new events to compress (last compaction at {last_compaction_idx})")
            return None

        # Get events to compress
        events_to_compress = events[start_idx:end_idx]

        # Calculate size BEFORE truncation
        compress_chars_before = 0
        for event in events_to_compress:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        compress_chars_before += len(part.text)

        logger.warning(
            f"[Compression] Will compress events {start_idx}:{end_idx} "
            f"({len(events_to_compress)} events, ~{compress_chars_before // 4} tokens before truncation)"
        )

        # PREPROCESSING: Truncate large texts in events to compress
        _truncate_large_event_texts(events_to_compress)

        # Calculate size AFTER truncation
        compress_chars_after = 0
        for event in events_to_compress:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        compress_chars_after += len(part.text)

        logger.info(
            f"[Compression] After truncation: ~{compress_chars_after // 4} tokens "
            f"(reduced from ~{compress_chars_before // 4})"
        )

        try:
            # Generate summary with LLM
            summary_text = await _create_event_summary_with_llm(
                events=events_to_compress,
                model_name=model_name,
                session_service=ctx.session_service,
                session=session,
            )

            # Apply compression
            await _compress_session_events(
                session=session,
                start_idx=start_idx,
                end_idx=end_idx,
                summary_text=summary_text,
                session_service=ctx.session_service,
            )

        except Exception as e:
            logger.error(f"[Compression] Failed to compress events: {e}", exc_info=True)

        # Return None to allow normal event flow
        return None

    return compression_callback


async def compress_events_manually(
    ctx,
    event_threshold: int = DEFAULT_EVENT_THRESHOLD,
    overlap_size: int = DEFAULT_OVERLAP_SIZE,
    model_name: Optional[str] = None,
):
    """
    Manually trigger event compression outside of callbacks.

    This is useful for triggering compression at specific points in the
    orchestration flow, such as after the implementation loop completes.

    Parameters
    ----------
    ctx : InvocationContext
        Invocation context with session access
    event_threshold : int, optional
        Minimum events before compression (default: 30)
    overlap_size : int, optional
        Events to keep uncompressed (default: 10)
    model_name : str, optional
        Model name string for summarization (default: DEFAULT_MODEL_NAME)
    """
    if model_name is None:
        model_name = DEFAULT_MODEL_NAME

    session = ctx.session
    events = session.events
    event_count = len(events)

    # Check if compression is needed
    if event_count <= event_threshold:
        logger.debug(f"[ManualCompression] Event count {event_count} below threshold, skipping")
        return

    logger.info(f"[ManualCompression] Compressing {event_count} events...")

    # Determine compression range
    end_idx = event_count - overlap_size

    if end_idx <= 0:
        logger.warning("[ManualCompression] Not enough events to compress")
        return

    # Find last compaction
    last_compaction_idx = -1
    for i in range(len(events) - 1, -1, -1):
        if events[i].actions and events[i].actions.compaction:
            last_compaction_idx = i
            break

    start_idx = max(0, last_compaction_idx + 1)

    if start_idx >= end_idx:
        logger.debug("[ManualCompression] No new events to compress")
        return

    events_to_compress = events[start_idx:end_idx]

    logger.info(f"[ManualCompression] Compressing {len(events_to_compress)} events ({start_idx}:{end_idx})")

    # PREPROCESSING: Truncate large texts
    _truncate_large_event_texts(events_to_compress)

    try:
        # Generate summary
        summary_text = await _create_event_summary_with_llm(
            events=events_to_compress,
            model_name=model_name,
            session_service=ctx.session_service,
            session=session,
        )

        # Apply compression
        await _compress_session_events(
            session=session,
            start_idx=start_idx,
            end_idx=end_idx,
            summary_text=summary_text,
            session_service=ctx.session_service,
        )

    except Exception as e:
        logger.error(f"[ManualCompression] Failed: {e}", exc_info=True)


def create_hard_limit_callback(max_events: int = 50):
    """
    Create a hard limit callback that keeps only the most recent N events.

    This is a safety mechanism that works alongside compression to ensure
    the event list never grows beyond a maximum size. Unlike compression,
    this simply discards old events without summarization.

    This should be used as a LAST RESORT when compression alone isn't
    sufficient to control context size.

    Parameters
    ----------
    max_events : int, optional
        Maximum number of events to keep (default: 50)

    Returns
    -------
    Callable
        Callback function for after_agent_callback

    Examples
    --------
    >>> callback = create_hard_limit_callback(max_events=50)
    >>> agent = LlmAgent(
    ...     name="my_agent",
    ...     instruction="...",
    ...     after_agent_callback=callback,
    ... )
    """

    def hard_limit_callback(callback_context: CallbackContext):
        """
        Trim history to keep only the most recent events.

        This is similar to the working example provided - it directly
        assigns to session.events to ensure changes take effect.
        """
        session = callback_context._invocation_context.session
        events = session.events

        logger.info(f"[HardLimit] Checking event count: {len(events)} events, max={max_events}")

        if len(events) > max_events:
            original_count = len(events)
            discarded_count = original_count - max_events

            # Get event authors for logging
            discarded_events = events[:discarded_count]
            discarded_authors = [getattr(e, 'author', 'unknown') for e in discarded_events[:5]]

            # CRITICAL: Direct assignment like working example
            session.events = events[-max_events:]

            logger.warning(
                f"[HardLimit] Trimmed from {original_count} to {len(session.events)} events. "
                f"Discarded {discarded_count} events, first 5 authors: {discarded_authors}"
            )
        else:
            logger.debug(f"[HardLimit] No trimming needed: {len(events)} <= {max_events}")

        return None

    return hard_limit_callback
