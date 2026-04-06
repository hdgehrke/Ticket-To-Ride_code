"""
Game state for Ticket to Ride: Europe.

All mutable state lives here.  Use copy.deepcopy(state) to snapshot.
"""
from __future__ import annotations
import copy
import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

from .info import (
    NUM_TRAINS, NUM_STATIONS, COLOR_CARD_COUNT, COLORS, LOCO,
    INITIAL_TICKET_LONG_DEAL, INITIAL_TICKET_REGULAR_DEAL, TURN_TICKET_DEAL,
)
from .routes import (
    TICKETS, DestinationTicket, get_ticket_set,
    EXPANSION_BASE, EXPANSION_BIG_CITIES, EXPANSION_MEGA,
)
from .board import Board, RouteSegment


class GamePhase(Enum):
    MEGA_LONG_SELECTION = auto()       # Mega Europe only: choose 0 or 1 long route from 2 dealt
    INITIAL_TICKET_SELECTION = auto()  # all players choosing initial tickets
    MAIN_TURN = auto()                 # current player selects their action
    SECOND_DRAW = auto()               # current player draws their 2nd card
    TICKET_SELECTION = auto()          # current player keeps ≥1 drawn ticket
    FINAL_ROUND = auto()               # last round after someone hits ≤2 trains
    GAME_OVER = auto()


@dataclass
class PlayerState:
    player_id: int
    hand: Dict[str, int] = field(default_factory=lambda: {c: 0 for c in COLORS + [LOCO]})
    tickets: List[DestinationTicket] = field(default_factory=list)
    trains: int = NUM_TRAINS
    stations: int = NUM_STATIONS
    score: int = 0          # running score from route claims
    station_cities: List[str] = field(default_factory=list)  # cities where stations are placed

    def hand_total(self) -> int:
        return sum(self.hand.values())

    def add_card(self, color: str) -> None:
        self.hand[color] = self.hand.get(color, 0) + 1

    def has_cards(self, color: str, count: int, locos_used: int = 0) -> bool:
        """Can the player pay `count` cards of `color`, using up to `locos_used` locomotives?"""
        needed = count - self.hand.get(color, 0)
        if needed <= 0:
            return True
        return needed <= locos_used and self.hand.get(LOCO, 0) >= needed

    def pay_cards(self, color: str, count: int, locos_used: int = 0) -> None:
        """Deduct cards from hand. Raises ValueError if insufficient."""
        color_count = self.hand.get(color, 0)
        color_pay = min(count, color_count)
        loco_pay = count - color_pay
        if loco_pay > locos_used or self.hand.get(LOCO, 0) < loco_pay:
            raise ValueError(f"Insufficient cards: need {count}×{color} (locos={locos_used})")
        self.hand[color] = color_count - color_pay
        self.hand[LOCO] = self.hand.get(LOCO, 0) - loco_pay


@dataclass
class GameState:
    board: Board
    players: List[PlayerState]
    # Card decks
    deck: List[str]                   # face-down draw pile
    discard: List[str]                # discard pile
    face_up: List[str]                # 5 face-up cards (None = empty slot)
    # Destination tickets
    ticket_deck: List[DestinationTicket]
    # Which expansion is being played (affects ticket setup and some rules)
    expansion: str = EXPANSION_BASE
    # Remaining long-route tickets (dealt 1 per player during initial selection; extras removed)
    long_ticket_deck: List[DestinationTicket] = field(default_factory=list)
    # Mega Europe only: did the current player keep a long route in MEGA_LONG_SELECTION?
    mega_long_kept: bool = False
    # Route ownership: route_index (into board.routes) → player_id
    claimed_routes: Dict[int, int] = field(default_factory=dict)
    # Turn state
    current_player: int = 0
    phase: GamePhase = GamePhase.INITIAL_TICKET_SELECTION
    # Tracks which player initiated the final round (triggered ≤2 trains)
    final_round_starter: Optional[int] = None
    # During INITIAL_TICKET_SELECTION / TICKET_SELECTION: pending tickets for current player
    pending_tickets: List[DestinationTicket] = field(default_factory=list)
    # How many players have finished initial ticket selection
    init_tickets_done: int = 0
    # During SECOND_DRAW: whether first draw was from face-up (and which slot)
    first_draw_was_loco: bool = False


def build_deck(rng: random.Random) -> List[str]:
    """Build and shuffle the full 110-card train card deck."""
    deck = []
    for color, count in COLOR_CARD_COUNT.items():
        deck.extend([color] * count)
    rng.shuffle(deck)
    return deck


def setup_game(num_players: int, seed: Optional[int] = None,
               expansion: str = EXPANSION_BASE) -> GameState:
    """
    Initialize a new game for 2–5 players.

    - Deals 4 train cards to each player
    - Sets up 5 face-up cards
    - Deals INITIAL_TICKET_DEAL destination tickets to each player for selection
    """
    if not (2 <= num_players <= 5):
        raise ValueError("TTR Europe supports 2–5 players")

    rng = random.Random(seed)
    board = Board()

    # Build and shuffle train card deck
    deck = build_deck(rng)
    discard: List[str] = []

    # Deal 4 train cards to each player
    players = [PlayerState(player_id=i) for i in range(num_players)]
    for player in players:
        for _ in range(4):
            player.add_card(deck.pop())

    # Set up 5 face-up cards
    face_up: List[str] = []
    for _ in range(5):
        face_up.append(deck.pop())
    # If 3+ locomotives face-up, reshuffle face-up into deck and redraw
    face_up, deck, discard = _fix_face_up(face_up, deck, discard, rng)

    # Separate and shuffle long-route vs. regular destination tickets
    long_tickets, regular_tickets = get_ticket_set(expansion)
    rng.shuffle(long_tickets)
    rng.shuffle(regular_tickets)

    ticket_deck = regular_tickets
    pending: List[DestinationTicket] = []
    initial_phase: GamePhase

    if expansion == EXPANSION_MEGA:
        # Mega Europe: deal 2 long tickets to first player; they choose 0 or 1 to keep.
        # Regular initial selection follows separately (5 tickets).
        # All 12 long tickets are shuffled; deal 2 per player (extras removed after selection).
        long_deck = long_tickets  # all 12 dealt 2 at a time during selection
        pending = [long_deck.pop(), long_deck.pop()]
        initial_phase = GamePhase.MEGA_LONG_SELECTION
    elif expansion == EXPANSION_BIG_CITIES:
        # Big Cities: no long routes; deal 5 big-city regular tickets to first player.
        long_deck = []
        pending = [ticket_deck.pop() for _ in range(min(5, len(ticket_deck)))]
        initial_phase = GamePhase.INITIAL_TICKET_SELECTION
    else:
        # Base, 1912, Europe Expanded: deal 1 long + 3 regular to first player.
        # Unused long tickets (beyond 1 per player) are removed from the game.
        long_deck = long_tickets[:num_players]  # one per player; rest go to box
        if long_deck:
            pending.append(long_deck.pop())
        for _ in range(min(INITIAL_TICKET_REGULAR_DEAL, len(ticket_deck))):
            pending.append(ticket_deck.pop())
        initial_phase = GamePhase.INITIAL_TICKET_SELECTION

    return GameState(
        board=board,
        players=players,
        deck=deck,
        discard=discard,
        face_up=face_up,
        ticket_deck=ticket_deck,
        expansion=expansion,
        long_ticket_deck=long_deck,
        current_player=0,
        phase=initial_phase,
        pending_tickets=pending,
        init_tickets_done=0,
    )


def _fix_face_up(face_up: List[str], deck: List[str],
                 discard: List[str], rng: random.Random,
                 max_attempts: int = 10) -> Tuple[List[str], List[str], List[str]]:
    """
    If 3 or more face-up cards are locomotives, return all face-up cards to the
    discard pile, reshuffle, and redeal 5 new face-up cards.
    Repeat up to max_attempts times.
    """
    for _ in range(max_attempts):
        loco_count = sum(1 for c in face_up if c == LOCO)
        if loco_count < 3:
            break
        discard.extend(face_up)
        face_up = []
        if len(deck) < 5:
            deck.extend(discard)
            discard = []
            rng.shuffle(deck)
        for _ in range(5):
            if not deck:
                break
            face_up.append(deck.pop())
    return face_up, deck, discard


def draw_card_from_deck(state: GameState, rng: random.Random) -> Optional[str]:
    """
    Draw one card from the face-down deck.  If deck is empty, shuffle discard
    into deck.  Returns None if no cards available at all.
    """
    if not state.deck:
        if not state.discard:
            return None
        state.deck = state.discard[:]
        state.discard = []
        rng.shuffle(state.deck)
    return state.deck.pop()


def replenish_face_up(state: GameState, slot: int, rng: random.Random) -> None:
    """Replace a taken face-up card and enforce the 3-loco rule."""
    card = draw_card_from_deck(state, rng)
    if card is not None:
        state.face_up[slot] = card
    else:
        # No cards left to replenish
        state.face_up[slot] = None  # type: ignore[assignment]
    state.face_up, state.deck, state.discard = _fix_face_up(
        state.face_up, state.deck, state.discard, rng
    )
