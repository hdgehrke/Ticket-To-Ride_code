"""
Flat discrete action space for the TTR Europe PettingZoo/RLlib environment.

Layout:
  [0..4]          DRAW_FACE_UP(slot 0..4)          — first draw in MAIN_TURN
  [5]             DRAW_DECK                         — draw 2 from deck (whole turn)
  [6]             DRAW_TICKETS                      — draw destination tickets
  [7..11]         DRAW_FACE_UP_SECOND(slot 0..4)   — second draw in SECOND_DRAW
  [12]            DRAW_DECK_SECOND                  — second draw from deck
  [13..27]        KEEP_TICKETS(mask 1..15)          — keep subset of up to 4 drawn tickets
  [28..59]        KEEP_INIT_TICKETS(mask 0..31)     — keep subset of up to 5 initial tickets
                    mask=0 = keep none (used in Mega Europe long-route selection)
  [60..60+R*9-1]  CLAIM_ROUTE(route_idx, color_idx)
                    color_idx 0..7 = COLORS index, 8 = loco-only (for ferry remainder)
  [60+R*9..]      PLACE_STATION(city_idx, color_idx) (color_idx 0..7=color, 8=loco)

  R = total number of route segments in the board (populated dynamically).

Call `ActionSpace(board)` to compute the mapping for a specific board instance.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import IntEnum
from typing import Dict, List, Optional, Tuple

from .board import Board
from .info import COLORS, LOCO


class ActionType(IntEnum):
    DRAW_FACE_UP = 0
    DRAW_DECK = 1
    DRAW_TICKETS = 2
    DRAW_FACE_UP_SECOND = 3
    DRAW_DECK_SECOND = 4
    KEEP_TICKETS = 5
    KEEP_INIT_TICKETS = 6
    CLAIM_ROUTE = 7
    PLACE_STATION = 8


@dataclass(frozen=True)
class Action:
    action_type: ActionType
    slot: int = 0      # face-up slot (0-4), or keep-mask (1-15), or route_idx, or city_idx
    color_idx: int = 0 # for CLAIM_ROUTE / PLACE_STATION (index into COLORS, or 8=loco-only)

    @property
    def color(self) -> str:
        if self.color_idx < len(COLORS):
            return COLORS[self.color_idx]
        return LOCO  # loco-only (color_idx == 8)

    def __str__(self) -> str:
        t = self.action_type
        if t == ActionType.DRAW_FACE_UP:
            return f"DrawFaceUp(slot={self.slot})"
        if t == ActionType.DRAW_DECK:
            return "DrawDeck"
        if t == ActionType.DRAW_TICKETS:
            return "DrawTickets"
        if t == ActionType.DRAW_FACE_UP_SECOND:
            return f"DrawFaceUpSecond(slot={self.slot})"
        if t == ActionType.DRAW_DECK_SECOND:
            return "DrawDeckSecond"
        if t == ActionType.KEEP_TICKETS:
            return f"KeepTickets(mask={self.slot:03b})"
        if t == ActionType.KEEP_INIT_TICKETS:
            return f"KeepInitTickets(mask={self.slot:04b})"
        if t == ActionType.CLAIM_ROUTE:
            return f"ClaimRoute(route={self.slot}, color={self.color})"
        if t == ActionType.PLACE_STATION:
            return f"PlaceStation(city={self.slot}, color={self.color})"
        return f"Action({t}, {self.slot}, {self.color_idx})"


class ActionSpace:
    """
    Computes the flat action index ↔ Action mapping for a given board.
    Create once and reuse throughout a game / training run.
    """

    # Static offsets for action types that don't depend on board size
    DRAW_FACE_UP_BASE = 0          # slots 0-4
    DRAW_DECK_IDX = 5
    DRAW_TICKETS_IDX = 6
    DRAW_FACE_UP_SECOND_BASE = 7   # slots 0-4
    DRAW_DECK_SECOND_IDX = 12
    KEEP_TICKETS_BASE = 13         # masks 1..15  (up to 4 drawn tickets)
    KEEP_INIT_TICKETS_BASE = 28    # masks 0..31  (up to 5 initial tickets; 0=keep none for Mega)
    CLAIM_ROUTE_BASE = 60

    NUM_COLORS_PER_ROUTE = 9   # 8 COLORS + 1 loco-only slot
    NUM_COLORS_PER_STATION = 9  # 8 COLORS + 1 loco slot (locomotives can pay for stations)

    def __init__(self, board: Board) -> None:
        self.board = board
        self.num_routes = len(board.routes)
        self.num_cities = len(board.cities)
        self.city_index: Dict[str, int] = {c: i for i, c in enumerate(board.cities)}

        self.PLACE_STATION_BASE = (
            self.CLAIM_ROUTE_BASE + self.num_routes * self.NUM_COLORS_PER_ROUTE
        )
        self.total = self.PLACE_STATION_BASE + self.num_cities * self.NUM_COLORS_PER_STATION

        # Build idx → Action and Action → idx mappings
        self._idx_to_action: List[Action] = [None] * self.total  # type: ignore
        self._action_to_idx: Dict[Action, int] = {}
        self._build_mapping()

    def _register(self, idx: int, action: Action) -> None:
        self._idx_to_action[idx] = action
        self._action_to_idx[action] = idx

    def _build_mapping(self) -> None:
        # Draw face-up (first draw)
        for s in range(5):
            a = Action(ActionType.DRAW_FACE_UP, slot=s)
            self._register(self.DRAW_FACE_UP_BASE + s, a)

        self._register(self.DRAW_DECK_IDX,    Action(ActionType.DRAW_DECK))
        self._register(self.DRAW_TICKETS_IDX, Action(ActionType.DRAW_TICKETS))

        # Draw face-up (second draw)
        for s in range(5):
            a = Action(ActionType.DRAW_FACE_UP_SECOND, slot=s)
            self._register(self.DRAW_FACE_UP_SECOND_BASE + s, a)

        self._register(self.DRAW_DECK_SECOND_IDX, Action(ActionType.DRAW_DECK_SECOND))

        # Keep tickets during turn (up to 4 tickets, masks 1..15)
        for mask in range(1, 16):
            a = Action(ActionType.KEEP_TICKETS, slot=mask)
            self._register(self.KEEP_TICKETS_BASE + mask - 1, a)

        # Keep initial tickets (up to 5 tickets, masks 0..31; mask=0 = keep none for Mega)
        for mask in range(0, 32):
            a = Action(ActionType.KEEP_INIT_TICKETS, slot=mask)
            self._register(self.KEEP_INIT_TICKETS_BASE + mask, a)

        # Claim route
        for route_idx in range(self.num_routes):
            for color_idx in range(self.NUM_COLORS_PER_ROUTE):
                idx = self.CLAIM_ROUTE_BASE + route_idx * self.NUM_COLORS_PER_ROUTE + color_idx
                a = Action(ActionType.CLAIM_ROUTE, slot=route_idx, color_idx=color_idx)
                self._register(idx, a)

        # Place station (8 regular colors + loco = 9 payment options)
        for city_idx in range(self.num_cities):
            for color_idx in range(self.NUM_COLORS_PER_STATION):
                idx = self.PLACE_STATION_BASE + city_idx * self.NUM_COLORS_PER_STATION + color_idx
                a = Action(ActionType.PLACE_STATION, slot=city_idx, color_idx=color_idx)
                self._register(idx, a)

    def decode(self, idx: int) -> Action:
        return self._idx_to_action[idx]

    def encode(self, action: Action) -> int:
        return self._action_to_idx[action]

    def claim_route_idx(self, route_idx: int, color_idx: int) -> int:
        return self.CLAIM_ROUTE_BASE + route_idx * self.NUM_COLORS_PER_ROUTE + color_idx

    def place_station_idx(self, city_idx: int, color_idx: int) -> int:
        return self.PLACE_STATION_BASE + city_idx * self.NUM_COLORS_PER_STATION + color_idx
