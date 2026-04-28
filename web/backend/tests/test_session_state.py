"""Pure unit tests for the session state machine — no DB, no HTTP."""

import pytest

from app.services.session_state import (
    InvalidTransition,
    SessionStatus,
    assert_transition,
    coerce_status,
)


class TestAssertTransition:
    def test_valid_string_input_returns_normalized_status(self):
        result = assert_transition("created", SessionStatus.PARSING)
        assert result is SessionStatus.CREATED

    def test_valid_enum_input_returns_same_enum(self):
        result = assert_transition(SessionStatus.PARSING, SessionStatus.PARSED)
        assert result is SessionStatus.PARSING

    def test_completed_to_parsing_is_allowed(self):
        # Re-parse after completion is an explicit design affordance
        result = assert_transition("completed", SessionStatus.PARSING)
        assert result is SessionStatus.COMPLETED

    def test_error_to_parsing_is_allowed(self):
        result = assert_transition("error", SessionStatus.PARSING)
        assert result is SessionStatus.ERROR

    def test_created_to_completed_raises(self):
        with pytest.raises(InvalidTransition, match="created"):
            assert_transition("created", SessionStatus.COMPLETED)

    def test_generating_to_confirmed_raises(self):
        with pytest.raises(InvalidTransition, match="generating"):
            assert_transition("generating", SessionStatus.CONFIRMED)

    def test_none_input_raises_via_coerce(self):
        # None coerces to ERROR; ERROR → COMPLETED is not allowed
        with pytest.raises(InvalidTransition, match="error"):
            assert_transition(None, SessionStatus.COMPLETED)

    def test_unknown_string_coerces_to_error(self):
        with pytest.raises(InvalidTransition, match="error"):
            assert_transition("nonexistent-status", SessionStatus.COMPLETED)


class TestCoerceStatus:
    def test_passes_through_enum_member(self):
        assert coerce_status(SessionStatus.CONFIRMED) is SessionStatus.CONFIRMED

    def test_converts_valid_string(self):
        assert coerce_status("confirmed") is SessionStatus.CONFIRMED

    def test_returns_error_for_none(self):
        assert coerce_status(None) is SessionStatus.ERROR

    def test_returns_error_for_unknown_string(self):
        assert coerce_status("legacy-unknown") is SessionStatus.ERROR

    @pytest.mark.parametrize("status", list(SessionStatus))
    def test_roundtrips_all_statuses_via_value(self, status: SessionStatus):
        assert coerce_status(status.value) is status
