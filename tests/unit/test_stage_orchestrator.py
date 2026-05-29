"""Unit tests for StageOrchestratorAgent truthful status logic."""

import uuid
from unittest.mock import patch

import pytest

from agentic_data_scientist.agents.adk.stage_orchestrator import StageOrchestratorAgent


class _FakeAgent:
    """Minimal stand-in for an ADK sub-agent whose run_async mutates session state."""

    def __init__(self, name, on_run=None):
        self.name = name
        self._on_run = on_run

    async def run_async(self, ctx):
        if self._on_run is not None:
            self._on_run(ctx)
        # Make this an async generator that yields nothing.
        if False:  # pragma: no cover
            yield


async def _noop_async(*args, **kwargs):
    """No-op replacement for compress_events_manually during tests."""
    return None


def _make_orchestrator(impl_on_run=None, crit_on_run=None, refl_on_run=None):
    return StageOrchestratorAgent(
        implementation_loop=_FakeAgent("implementation_loop", impl_on_run),
        criteria_checker=_FakeAgent("criteria_checker", crit_on_run),
        stage_reflector=_FakeAgent("stage_reflector", refl_on_run),
    )


async def _make_ctx(orchestrator, stages, criteria):
    from google.adk.agents import InvocationContext
    from google.adk.sessions import InMemorySessionService

    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name="test", user_id="test_user", session_id="test_session")
    session.state["high_level_stages"] = stages
    session.state["high_level_success_criteria"] = criteria

    ctx = InvocationContext(
        session=session,
        session_service=session_service,
        invocation_id=str(uuid.uuid4()),
        agent=orchestrator,
    )
    return ctx, session


async def _run(orchestrator, ctx):
    events = []
    with patch(
        "agentic_data_scientist.agents.adk.stage_orchestrator.compress_events_manually",
        new=_noop_async,
    ):
        async for ev in orchestrator._run_async_impl(ctx):
            events.append(ev)
    return events


# --- Scenario callbacks -----------------------------------------------------


def _impl_approved(ctx):
    ctx.session.state["implementation_summary"] = "done"
    ctx.session.state["implementation_review_confirmation_decision"] = {"exit": True, "reason": "approved"}


def _impl_not_approved(ctx):
    ctx.session.state["implementation_summary"] = "partial"
    ctx.session.state["implementation_review_confirmation_decision"] = {"exit": False, "reason": "more work"}


def _mark_all_criteria_met(ctx):
    for c in ctx.session.state["high_level_success_criteria"]:
        c["met"] = True


class TestApplyTerminalStatus:
    """Direct tests of the pure status-derivation logic."""

    def test_completed_when_all_met_and_approved(self):
        orch = _make_orchestrator()
        state = {
            "high_level_success_criteria": [{"index": 0, "criteria": "c0", "met": True}],
            "high_level_stages": [{"index": 0, "title": "s0", "approved": True}],
        }
        info = orch._apply_terminal_status(state)
        assert info["run_status"] == "completed"
        assert state["run_status"] == "completed"
        assert "all success criteria were met" in state["unmet_criteria_summary"]
        assert "all attempted stages were approved" in state["unapproved_stages_summary"]

    def test_completed_with_warnings_when_met_but_unapproved(self):
        orch = _make_orchestrator()
        state = {
            "high_level_success_criteria": [{"index": 0, "criteria": "c0", "met": True}],
            "high_level_stages": [{"index": 0, "title": "Stage Zero", "approved": False}],
        }
        info = orch._apply_terminal_status(state)
        assert info["run_status"] == "completed_with_warnings"
        assert state["run_status"] == "completed_with_warnings"
        assert "Stage Zero" in state["unapproved_stages_summary"]

    def test_incomplete_when_criteria_unmet(self):
        orch = _make_orchestrator()
        state = {
            "high_level_success_criteria": [
                {"index": 0, "criteria": "c0", "met": True},
                {"index": 1, "criteria": "Crit One", "met": False},
            ],
            "high_level_stages": [{"index": 0, "title": "s0", "approved": True}],
        }
        info = orch._apply_terminal_status(state)
        assert info["run_status"] == "incomplete"
        assert state["run_status"] == "incomplete"
        assert "Crit One" in state["unmet_criteria_summary"]

    def test_unattempted_stage_not_counted_as_unapproved(self):
        orch = _make_orchestrator()
        state = {
            "high_level_success_criteria": [{"index": 0, "criteria": "c0", "met": True}],
            # Stage without an "approved" key was never attempted.
            "high_level_stages": [{"index": 0, "title": "s0"}],
        }
        info = orch._apply_terminal_status(state)
        assert info["run_status"] == "completed"


class TestFormatStatusBlock:
    """Tests for the user-facing status text block."""

    def test_empty_when_nothing_outstanding(self):
        orch = _make_orchestrator()
        assert orch._format_status_block({"unmet": [], "unapproved": []}) == ""

    def test_lists_unmet_and_unapproved(self):
        orch = _make_orchestrator()
        block = orch._format_status_block(
            {
                "unmet": [{"index": 0, "criteria": "Crit X"}],
                "unapproved": [{"index": 1, "title": "Stage Y"}],
            }
        )
        assert "Crit X" in block
        assert "Stage Y" in block


@pytest.mark.asyncio
class TestOrchestratorStatusFlow:
    """End-to-end orchestration runs with mocked sub-agents."""

    async def test_completed_when_approved_and_criteria_met(self):
        orch = _make_orchestrator(impl_on_run=_impl_approved, crit_on_run=_mark_all_criteria_met)
        ctx, session = await _make_ctx(
            orch,
            stages=[{"index": 0, "title": "Stage A", "description": "do A"}],
            criteria=[{"index": 0, "criteria": "Crit A", "met": False}],
        )

        await _run(orch, ctx)

        assert session.state["run_status"] == "completed"
        stage = session.state["high_level_stages"][0]
        assert stage["approved"] is True
        assert stage["status"] == "approved"

    async def test_completed_with_warnings_when_not_approved(self):
        orch = _make_orchestrator(impl_on_run=_impl_not_approved, crit_on_run=_mark_all_criteria_met)
        ctx, session = await _make_ctx(
            orch,
            stages=[{"index": 0, "title": "Stage A", "description": "do A"}],
            criteria=[{"index": 0, "criteria": "Crit A", "met": False}],
        )

        await _run(orch, ctx)

        assert session.state["run_status"] == "completed_with_warnings"
        stage = session.state["high_level_stages"][0]
        assert stage["approved"] is False
        assert stage["status"] == "needs_work"

    async def test_incomplete_when_criteria_never_met(self):
        # Implementation is approved, but the criteria checker never marks criteria met.
        orch = _make_orchestrator(impl_on_run=_impl_approved, crit_on_run=None)
        ctx, session = await _make_ctx(
            orch,
            stages=[{"index": 0, "title": "Stage A", "description": "do A"}],
            criteria=[{"index": 0, "criteria": "Crit A", "met": False}],
        )

        await _run(orch, ctx)

        assert session.state["run_status"] == "incomplete"
        assert "Crit A" in session.state["unmet_criteria_summary"]
