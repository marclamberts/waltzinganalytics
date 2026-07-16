"""Opta (Stats Perform) F24 event-feed constants used to identify set pieces.

The F24 feed encodes every action as an ``event`` with a numeric ``typeId``
and a list of ``qualifier`` objects (each carrying a numeric ``qualifierId``
and, often, a string ``value``). Set pieces are not their own event type --
they are ordinary events (mostly passes, ``typeId == 1``) carrying a
qualifier that flags the restart type.

The IDs below are the standard Opta/Stats Perform qualifier vocabulary and
were cross-checked against a real F24 match export (see
``tests/data/sample_match.json``): each qualifier's tagged events line up
with the expected pitch location (e.g. qualifier 279 "Kick off" events sit
at the centre spot, qualifier 6 "Corner taken" events sit in the corner
arcs, qualifier 107 "Throw-in" events sit on the touchline, and qualifier
124 "Goal kick" events sit on the six-yard line).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Event typeId
# ---------------------------------------------------------------------------
TYPE_PASS = 1
TYPE_OFFSIDE_PASS = 2
TYPE_TAKE_ON = 3
TYPE_FOUL = 4
TYPE_OUT = 5
TYPE_CORNER_AWARDED = 6
TYPE_TACKLE = 7
TYPE_INTERCEPTION = 8
TYPE_SAVE = 10
TYPE_CLAIM = 11
TYPE_CLEARANCE = 12
TYPE_MISS = 13
TYPE_POST = 14
TYPE_ATTEMPT_SAVED = 15
TYPE_GOAL = 16
TYPE_CARD = 17
TYPE_PLAYER_OFF = 18
TYPE_PLAYER_ON = 19
TYPE_START = 32
TYPE_TEAM_SET_UP = 34
TYPE_FORMATION_CHANGE = 40
TYPE_AERIAL = 44

# Shot-like event types (used to detect goals/shots resulting from a set piece)
SHOT_TYPE_IDS = frozenset({TYPE_MISS, TYPE_POST, TYPE_ATTEMPT_SAVED, TYPE_GOAL})

# ---------------------------------------------------------------------------
# Qualifiers that flag *how* an event was played
# ---------------------------------------------------------------------------
QUALIFIER_LONG_BALL = 1
QUALIFIER_CROSS = 2
QUALIFIER_HEAD_PASS = 3
QUALIFIER_THROUGH_BALL = 4
QUALIFIER_FREE_KICK_TAKEN = 5
QUALIFIER_CORNER_TAKEN = 6
QUALIFIER_PLAYERS_CAUGHT_OFFSIDE = 7
QUALIFIER_DIRECT = 9  # also reused as "Penalty" flag on shot events, see below
QUALIFIER_PENALTY = 9
QUALIFIER_NOT_ASSISTED = 26
QUALIFIER_ASSISTED = 28
QUALIFIER_ASSIST = 29
QUALIFIER_RELATED_EVENT_ID = 55
QUALIFIER_ZONE = 56
QUALIFIER_PASS_END_X = 140
QUALIFIER_PASS_END_Y = 141
QUALIFIER_KEEPER_THROW = 123
QUALIFIER_GOAL_KICK = 124
QUALIFIER_THROW_IN = 107
QUALIFIER_KICK_OFF = 279

# ---------------------------------------------------------------------------
# The six set-piece categories this package reports on, keyed by the
# qualifierId that identifies them on a `typeId == 1` (Pass) event.
# Penalties are the exception: they are identified on shot events instead.
# ---------------------------------------------------------------------------
SET_PIECE_QUALIFIERS = {
    "corner": QUALIFIER_CORNER_TAKEN,
    "free_kick": QUALIFIER_FREE_KICK_TAKEN,
    "throw_in": QUALIFIER_THROW_IN,
    "goal_kick": QUALIFIER_GOAL_KICK,
    "kick_off": QUALIFIER_KICK_OFF,
}

SET_PIECE_TYPES = ("penalty", "kick_off", "free_kick", "corner", "throw_in", "goal_kick")
