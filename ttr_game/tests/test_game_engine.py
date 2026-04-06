"""
Basic sanity tests for the TTR Europe game engine.
Run with: pytest ttr_game/tests/test_game_engine.py -v
"""
import copy
import random
import pytest

from ttr_game.game.board import Board
from ttr_game.game.info import COLORS, LOCO, NUM_TRAINS, NUM_STATIONS
from ttr_game.game.routes import TICKETS, ALL_TICKETS, find_ticket, get_ticket_set, EXPANSION_1912, EXPANSION_BIG_CITIES
from ttr_game.game.state import setup_game, GamePhase
from ttr_game.game.actions import ActionSpace, ActionType
from ttr_game.game.rules import legal_actions, step, final_scores, is_terminal


# ---------------------------------------------------------------------------
# Board tests
# ---------------------------------------------------------------------------

def test_board_loads():
    board = Board()
    assert len(board.cities) >= 40, "Should have ~46 cities"
    assert len(board.routes) >= 50, "Should have many route segments"


def test_no_bacelona_typo():
    board = Board()
    assert "Bacelona" not in board.cities
    assert "Barcelona" in board.cities


def test_double_routes_expanded():
    """Madrid↔Pamplona is a double route; should produce 2 route segments."""
    board = Board()
    segments = board.routes_between("Madrid", "Pamplona")
    assert len(segments) == 2, f"Expected 2 parallel routes, got {len(segments)}"
    colors = {s.color for s in segments}
    assert "K" in colors and "W" in colors


def test_neighbors_symmetric():
    """Each edge should appear in both directions in the adjacency list."""
    board = Board()
    for city in board.cities:
        for neighbor in board.neighbors(city):
            assert city in board.neighbors(neighbor), \
                f"Edge {city}↔{neighbor} is not symmetric"


def test_all_routes_have_valid_scoring():
    from ttr_game.game.info import TRAIN_SCORING
    board = Board()
    for route in board.routes:
        assert route.length in TRAIN_SCORING, \
            f"Route {route} has length {route.length} with no scoring entry"


# ---------------------------------------------------------------------------
# Ticket tests
# ---------------------------------------------------------------------------

def test_tickets_count():
    assert len(TICKETS) == 46, f"Expected 46 base tickets, got {len(TICKETS)}"
    long_base = [t for t in TICKETS if t.is_long]
    assert len(long_base) == 6, f"Expected 6 long base tickets, got {len(long_base)}"
    regular_base = [t for t in TICKETS if not t.is_long]
    assert len(regular_base) == 40, f"Expected 40 regular base tickets, got {len(regular_base)}"


def test_no_danzic_typo():
    board = Board()
    assert "Danzic" not in board.cities, "Found old typo 'Danzic' in board cities"
    assert "Danzig" in board.cities, "'Danzig' not found in board cities"


def test_expansion_ticket_counts():
    long_1912, reg_1912 = get_ticket_set(EXPANSION_1912)
    assert len(long_1912) == 6, f"1912 long tickets: expected 6, got {len(long_1912)}"
    # 40 base regular + 19 (1912-only) + 30 (1912 + Big Cities shared) = 89
    assert len(reg_1912) == 89, f"1912 regular tickets: expected 89, got {len(reg_1912)}"

    long_bc, reg_bc = get_ticket_set(EXPANSION_BIG_CITIES)
    # Big Cities does not use long routes
    assert len(long_bc) == 0, f"Big Cities long tickets: expected 0, got {len(long_bc)}"
    # 15 base big-city regular + 30 (1912 + Big Cities shared) = 45
    assert len(reg_bc) == 45, f"Big Cities regular tickets: expected 45, got {len(reg_bc)}"


def test_all_ticket_cities_on_board():
    """Every city mentioned in any ticket (all expansions) must exist on the board."""
    board = Board()
    for t in ALL_TICKETS:
        assert t.city1 in board.cities, f"Ticket city '{t.city1}' not on board (ticket: {t})"
        assert t.city2 in board.cities, f"Ticket city '{t.city2}' not on board (ticket: {t})"


def test_no_bucresti_typo():
    for ticket in TICKETS:
        assert "Bucresti" not in (ticket.city1, ticket.city2), \
            "Found typo 'Bucresti' in tickets"


def test_ticket_cities_on_board():
    board = Board()
    for ticket in TICKETS:
        assert ticket.city1 in board.cities, f"{ticket.city1} not in board"
        assert ticket.city2 in board.cities, f"{ticket.city2} not in board"


def test_expansion_games_complete():
    """Random games with all expansion variants should complete without deadlock."""
    from ttr_game.game.routes import EXPANSION_EUROPE_EXPANDED, EXPANSION_MEGA
    for exp in (EXPANSION_1912, EXPANSION_BIG_CITIES, EXPANSION_EUROPE_EXPANDED, EXPANSION_MEGA):
        rng = random.Random(7)
        state = setup_game(3, seed=7, expansion=exp)
        board = Board()
        asp = ActionSpace(board)
        for _ in range(8000):
            if is_terminal(state):
                break
            legal = legal_actions(state, asp)
            assert len(legal) > 0, f"Deadlock in {exp} game (phase={state.phase.name})"
            step(state, rng.choice(legal), asp, rng)
        assert is_terminal(state), f"{exp} game did not complete"


def test_mega_initial_selection():
    """Mega Europe starts with MEGA_LONG_SELECTION, then INITIAL_TICKET_SELECTION."""
    from ttr_game.game.routes import EXPANSION_MEGA
    state = setup_game(3, seed=5, expansion=EXPANSION_MEGA)
    board = Board()
    asp = ActionSpace(board)
    assert state.phase == GamePhase.MEGA_LONG_SELECTION
    assert len(state.pending_tickets) == 2
    assert all(t.is_long for t in state.pending_tickets)
    # Legal actions should allow keeping 0 or 1 long ticket
    legal = legal_actions(state, asp)
    for idx in legal:
        a = asp.decode(idx)
        assert a.action_type == ActionType.KEEP_INIT_TICKETS
        assert bin(a.slot).count('1') <= 1, f"Mega long selection allows mask with >1 bits: {a.slot}"


def test_big_cities_initial_deal_5():
    """Big Cities deals 5 tickets to first player (no long route)."""
    from ttr_game.game.routes import EXPANSION_BIG_CITIES
    state = setup_game(3, seed=5, expansion=EXPANSION_BIG_CITIES)
    assert state.phase == GamePhase.INITIAL_TICKET_SELECTION
    assert len(state.pending_tickets) == 5
    assert all(not t.is_long for t in state.pending_tickets)


# ---------------------------------------------------------------------------
# Game setup tests
# ---------------------------------------------------------------------------

def test_setup_2_players():
    state = setup_game(2, seed=42)
    assert len(state.players) == 2
    assert state.phase == GamePhase.INITIAL_TICKET_SELECTION
    for player in state.players:
        assert player.hand_total() == 4  # dealt 4 cards at start
        assert player.trains == NUM_TRAINS
        assert player.stations == NUM_STATIONS


def test_setup_5_players():
    state = setup_game(5, seed=0)
    assert len(state.players) == 5


def test_face_up_cards_not_3_locos():
    """Face-up must never have 3+ locomotives after setup."""
    for seed in range(20):
        state = setup_game(4, seed=seed)
        loco_count = sum(1 for c in state.face_up if c == LOCO)
        assert loco_count < 3, f"seed={seed}: {state.face_up} has {loco_count} locos"


def test_total_cards_dealt():
    """All 110 cards must be accounted for after setup."""
    state = setup_game(4, seed=1)
    total = (
        sum(p.hand_total() for p in state.players)
        + len(state.deck)
        + len(state.face_up)
        + len(state.discard)
    )
    assert total == 110, f"Expected 110 cards total, got {total}"


# ---------------------------------------------------------------------------
# Action space tests
# ---------------------------------------------------------------------------

def test_action_space_encoding_roundtrip():
    board = Board()
    asp = ActionSpace(board)
    for i in range(asp.total):
        action = asp.decode(i)
        assert asp.encode(action) == i, f"Round-trip failed at index {i}"


def test_legal_actions_nonempty_at_start():
    state = setup_game(2, seed=5)
    board = Board()
    asp = ActionSpace(board)
    legal = legal_actions(state, asp)
    assert len(legal) > 0, "Should have legal actions at game start"


def test_initial_ticket_selection_legal_actions():
    """During INITIAL_TICKET_SELECTION, only KEEP_INIT_TICKETS actions are legal."""
    state = setup_game(3, seed=7)
    board = Board()
    asp = ActionSpace(board)
    assert state.phase == GamePhase.INITIAL_TICKET_SELECTION
    legal = legal_actions(state, asp)
    for idx in legal:
        action = asp.decode(idx)
        assert action.action_type == ActionType.KEEP_INIT_TICKETS, \
            f"Expected KEEP_INIT_TICKETS, got {action}"


# ---------------------------------------------------------------------------
# Full game smoke test (random play until game over)
# ---------------------------------------------------------------------------

def test_random_game_completes():
    """Play a full game with random legal actions; verify it ends and scores sum correctly."""
    rng = random.Random(99)
    state = setup_game(3, seed=99)
    board = Board()
    asp = ActionSpace(board)

    max_steps = 5000
    for step_num in range(max_steps):
        if is_terminal(state):
            break
        legal = legal_actions(state, asp)
        assert len(legal) > 0, f"Deadlock at step {step_num}"
        action_idx = rng.choice(legal)
        step(state, action_idx, asp, rng)
    else:
        pytest.fail(f"Game did not complete within {max_steps} steps")

    assert is_terminal(state)
    scores = final_scores(state)
    assert len(scores) == 3
    assert all(isinstance(s, int) for s in scores)


def test_claimed_routes_not_double_claimed():
    """No route should be claimed by two different players."""
    rng = random.Random(42)
    state = setup_game(4, seed=42)
    board = Board()
    asp = ActionSpace(board)

    for _ in range(3000):
        if is_terminal(state):
            break
        legal = legal_actions(state, asp)
        if not legal:
            break
        action_idx = rng.choice(legal)
        step(state, action_idx, asp, rng)

    # Check no route is claimed twice
    claimed_indices = list(state.claimed_routes.keys())
    assert len(claimed_indices) == len(set(claimed_indices)), "Duplicate route claims!"


def test_double_route_blocked_in_3_player():
    """In a 3-player game, once one parallel route is claimed the other is blocked."""
    from ttr_game.game.rules import _find_parallel
    rng = random.Random(0)
    board = Board()
    asp = ActionSpace(board)
    state = setup_game(3, seed=0)

    # Finish initial ticket selection
    while state.phase.name == "INITIAL_TICKET_SELECTION":
        legal = legal_actions(state, asp)
        step(state, rng.choice(legal), asp, rng)

    # Find a double route pair
    double_pairs = []
    for i, route in enumerate(board.routes):
        partner = _find_parallel(board, i)
        if partner is not None and i < partner:
            double_pairs.append((i, partner))
    assert double_pairs, "No double routes found on board"

    route_a, route_b = double_pairs[0]
    # Force-claim route_a for player 0
    state.claimed_routes[route_a] = 0

    # Now route_b should not be in legal actions for any player
    for pid in range(3):
        state.current_player = pid
        state.phase = state.phase.__class__.MAIN_TURN
        # Give player plenty of cards
        for c in COLORS:
            state.players[pid].hand[c] = 10
        legal = legal_actions(state, asp)
        legal_claim = [idx for idx in legal if asp.decode(idx).action_type == ActionType.CLAIM_ROUTE]
        claimed_routes_in_legal = {asp.decode(idx).slot for idx in legal_claim}
        assert route_b not in claimed_routes_in_legal, \
            f"Player {pid} can claim parallel route {route_b} in 3-player game — should be blocked"


def test_initial_tickets_min_keep_2():
    """During initial ticket selection, players must keep at least 2 tickets."""
    board = Board()
    asp = ActionSpace(board)
    state = setup_game(4, seed=10)
    assert state.phase.name == "INITIAL_TICKET_SELECTION"
    legal = legal_actions(state, asp)
    for idx in legal:
        action = asp.decode(idx)
        assert action.action_type == ActionType.KEEP_INIT_TICKETS
        kept_count = bin(action.slot).count('1')
        assert kept_count >= 2, f"Action keeps only {kept_count} ticket(s); minimum is 2"


def test_initial_tickets_long_and_regular():
    """Each player's initial hand should contain exactly 1 long-route ticket."""
    board = Board()
    asp = ActionSpace(board)
    rng = random.Random(5)

    for num_players in (2, 3, 4, 5):
        state = setup_game(num_players, seed=num_players)
        # The first player's pending tickets should have exactly 1 long ticket
        long_count = sum(1 for t in state.pending_tickets if t.is_long)
        assert long_count == 1, \
            f"{num_players}p: player 0 has {long_count} long tickets, expected 1"
        assert len(state.pending_tickets) == 4, \
            f"{num_players}p: player 0 has {len(state.pending_tickets)} initial tickets, expected 4"


def test_station_loco_payment():
    """A player should be able to place a station using locomotives."""
    board = Board()
    asp = ActionSpace(board)
    state = setup_game(2, seed=1)

    # Skip initial ticket selection
    rng = random.Random(1)
    while state.phase.name == "INITIAL_TICKET_SELECTION":
        legal = legal_actions(state, asp)
        step(state, rng.choice(legal), asp, rng)

    # Give player 0 only locomotives (no regular cards)
    state.current_player = 0
    state.phase = state.phase.__class__.MAIN_TURN
    for c in COLORS:
        state.players[0].hand[c] = 0
    state.players[0].hand[LOCO] = 3

    legal = legal_actions(state, asp)
    station_actions = [idx for idx in legal if asp.decode(idx).action_type == ActionType.PLACE_STATION]
    assert len(station_actions) > 0, "Player with only locomotives should be able to place a station"


def test_station_city_uniqueness():
    """Two players cannot place stations in the same city."""
    board = Board()
    asp = ActionSpace(board)
    state = setup_game(2, seed=2)

    rng = random.Random(2)
    while state.phase.name == "INITIAL_TICKET_SELECTION":
        legal = legal_actions(state, asp)
        step(state, rng.choice(legal), asp, rng)

    # Player 0 already has a station in the first city of the board
    city = board.cities[0]
    state.players[0].station_cities.append(city)
    state.players[0].stations -= 1

    # Player 1 should not be able to place a station in that city
    state.current_player = 1
    state.phase = state.phase.__class__.MAIN_TURN
    for c in COLORS:
        state.players[1].hand[c] = 5
    state.players[1].hand[LOCO] = 5

    legal = legal_actions(state, asp)
    station_actions = [idx for idx in legal if asp.decode(idx).action_type == ActionType.PLACE_STATION]
    city_idx = board.cities.index(city)
    for idx in station_actions:
        action = asp.decode(idx)
        assert action.slot != city_idx, \
            f"Player 1 can place station at {city} already occupied by player 0"
