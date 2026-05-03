"""
Rules engine for Ticket to Ride: Europe.

Provides:
  - legal_actions(state, action_space) → List[int]
  - step(state, action_idx, action_space, rng) → reward (float)
  - final_scores(state) → List[int]
  - is_terminal(state) → bool

Tunnel mechanic (simplified for RL):
  When a player claims a tunnel route, 3 cards are drawn from the deck.
  If any of the 3 match the route color or are locomotives, the player must
  pay that many additional cards.  If the player cannot pay, the route claim
  fails (cards are returned) and their turn ends.

Station mechanic:
  Players may place up to 3 stations.  A station at a city lets the player
  "borrow" one incoming route claimed by another player when checking ticket
  completion.  Cost: 1/2/3 same-color cards for 1st/2nd/3rd station.
"""
from __future__ import annotations
import itertools
import random
from typing import Dict, List, Optional, Set, Tuple

from .actions import Action, ActionSpace, ActionType
from .board import Board, RouteSegment
from .info import (
    COLORS, LOCO, GRAY, FINAL_ROUND_TRIGGER, TRAIN_SCORING,
    LONGEST_ROUTE_BONUS, STATION_COSTS, TURN_TICKET_DEAL, TURN_TICKET_DEAL_BIG_CITIES,
    INITIAL_TICKET_LONG_DEAL, INITIAL_TICKET_REGULAR_DEAL, INITIAL_TICKET_MIN_KEEP,
)
from .routes import (
    EXPANSION_BIG_CITIES, EXPANSION_MEGA,
)
from .routes import DestinationTicket
from .state import (
    GamePhase, GameState, PlayerState,
    draw_card_from_deck, replenish_face_up,
)


# ---------------------------------------------------------------------------
# Legal action computation
# ---------------------------------------------------------------------------

def legal_actions(state: GameState, asp: ActionSpace) -> List[int]:
    """Return list of valid action indices for the current player in the current phase."""
    phase = state.phase
    player = state.players[state.current_player]

    if phase == GamePhase.GAME_OVER:
        return []

    if phase == GamePhase.TUNNEL_RESOLUTION:
        return [asp.TUNNEL_PAY_IDX, asp.TUNNEL_DECLINE_IDX]

    if phase == GamePhase.MEGA_LONG_SELECTION:
        return _legal_mega_long_actions(state, asp)

    if phase in (GamePhase.INITIAL_TICKET_SELECTION, GamePhase.TICKET_SELECTION):
        return _legal_ticket_keep_actions(state, asp)

    if phase == GamePhase.SECOND_DRAW:
        return _legal_second_draw_actions(state, asp, player)

    # MAIN_TURN or FINAL_ROUND
    actions: List[int] = []
    actions.extend(_legal_draw_first_actions(state, asp, player))
    actions.extend(_legal_claim_route_actions(state, asp, player))
    actions.extend(_legal_place_station_actions(state, asp, player))
    # Drawing tickets only allowed if ticket deck is non-empty
    if state.ticket_deck:
        actions.append(asp.DRAW_TICKETS_IDX)
    return actions


def _legal_draw_first_actions(state: GameState, asp: ActionSpace,
                               player: PlayerState) -> List[int]:
    actions = []
    cards_available = sum(1 for c in state.face_up if c is not None)
    deck_available = bool(state.deck or state.discard)

    if not (cards_available > 0 or deck_available):
        return []

    for slot, card in enumerate(state.face_up):
        if card is not None:
            actions.append(asp.DRAW_FACE_UP_BASE + slot)
    if deck_available:
        actions.append(asp.DRAW_DECK_IDX)
    return actions


def _legal_second_draw_actions(state: GameState, asp: ActionSpace,
                                player: PlayerState) -> List[int]:
    actions = []
    for slot, card in enumerate(state.face_up):
        # Cannot take a second locomotive from face-up
        if card is not None and card != LOCO:
            actions.append(asp.DRAW_FACE_UP_SECOND_BASE + slot)
    if state.deck or state.discard:
        actions.append(asp.DRAW_DECK_SECOND_IDX)
    return actions


def _legal_claim_route_actions(state: GameState, asp: ActionSpace,
                                player: PlayerState) -> List[int]:
    actions = []
    num_players = len(state.players)
    for route_idx, route in enumerate(state.board.routes):
        if route_idx in state.claimed_routes:
            continue  # already claimed
        # In 2–3 player games, once one route of a double pair is claimed the
        # parallel route is closed to ALL players for the rest of the game.
        if num_players <= 3:
            partner = _find_parallel(state.board, route_idx)
            if partner is not None and partner in state.claimed_routes:
                continue
        if player.trains < route.length:
            continue  # not enough trains
        color_actions = _claim_color_actions(route, player, route_idx, asp)
        actions.extend(color_actions)
    return actions


def _find_parallel(board: Board, route_idx: int) -> Optional[int]:
    """Return the index of the parallel route (same cities, different parallel_index), or None."""
    r = board.routes[route_idx]
    if r.parallel_index == 0:
        target_idx = 1
    else:
        target_idx = 0
    for i, other in enumerate(board.routes):
        if (other.city1 == r.city1 and other.city2 == r.city2
                and other.parallel_index == target_idx):
            return i
    return None


def _claim_color_actions(route: RouteSegment, player: PlayerState,
                         route_idx: int, asp: ActionSpace) -> List[int]:
    """
    Return valid (route_idx, color_idx) claim actions for a route given player's hand.

    Rules:
      - Colored route: must use that color (+ optional locomotives)
      - Gray route ("X"): any single color (+ optional locomotives)
      - Ferry routes: exactly `ferries` locomotives must be paid; rest can be any valid color
      - Tunnels: base cost is route.length cards; extra cost resolved at step time
    """
    actions = []
    length = route.length
    ferries = route.ferries
    remaining = length - ferries  # non-ferry cards needed

    candidate_colors: List[str]
    if route.color == GRAY:
        candidate_colors = COLORS[:]
    else:
        candidate_colors = [route.color]

    loco_in_hand = player.hand.get(LOCO, 0)
    can_pay_ferries = loco_in_hand >= ferries

    if not can_pay_ferries:
        return []

    for color in candidate_colors:
        color_idx = COLORS.index(color)
        color_count = player.hand.get(color, 0)
        locos_available = loco_in_hand - ferries

        # Can pay `remaining` cards using color + some locos
        for locos_used in range(min(locos_available, remaining) + 1):
            if color_count + locos_used >= remaining:
                actions.append(asp.claim_route_idx(route_idx, color_idx))
                break  # only need to add the action once per color

    return actions


def _legal_place_station_actions(state: GameState, asp: ActionSpace,
                                  player: PlayerState) -> List[int]:
    if player.stations == 0:
        return []
    station_num = NUM_STATIONS - player.stations  # 0, 1, or 2 stations already placed
    cost = STATION_COSTS[station_num]

    # Cities already occupied by any player's station
    occupied = {city for p in state.players for city in p.station_cities}

    actions = []
    for city_idx, city in enumerate(state.board.cities):
        if city in occupied:
            continue  # already has a station (any player)
        # Payment options: any single color, or locomotives
        for color_idx, color in enumerate(COLORS + [LOCO]):
            if player.hand.get(color, 0) >= cost:
                actions.append(asp.place_station_idx(city_idx, color_idx))
    return actions


def _legal_mega_long_actions(state: GameState, asp: ActionSpace) -> List[int]:
    """Mega Europe phase 1: player may keep 0 or exactly 1 of the 2 dealt long tickets."""
    n = len(state.pending_tickets)
    # mask=0 → keep none; single-bit masks → keep exactly one ticket
    valid_masks = [0] + [1 << i for i in range(n)]
    return [asp.KEEP_INIT_TICKETS_BASE + m for m in valid_masks]


def _legal_ticket_keep_actions(state: GameState, asp: ActionSpace) -> List[int]:
    n = len(state.pending_tickets)
    if n == 0:
        return []
    if state.phase == GamePhase.INITIAL_TICKET_SELECTION:
        if state.expansion == EXPANSION_MEGA:
            # Mega: keep ≥2 if already kept a long route, else ≥3
            min_keep = 2 if state.mega_long_kept else 3
        else:
            min_keep = INITIAL_TICKET_MIN_KEEP  # 2 for base/1912/big_cities/expanded
        min_keep = min(min_keep, n)
        valid_masks = [m for m in range(1, 2 ** n) if bin(m).count('1') >= min_keep]
        return [asp.KEEP_INIT_TICKETS_BASE + mask for mask in valid_masks]
    else:
        # During turn draws, must keep at least 1
        return [asp.KEEP_TICKETS_BASE + mask - 1 for mask in range(1, 2 ** n)]


# ---------------------------------------------------------------------------
# Step / action application
# ---------------------------------------------------------------------------

def step(state: GameState, action_idx: int, asp: ActionSpace,
         rng: random.Random) -> float:
    """
    Apply action_idx to state (mutates state in-place).
    Returns immediate reward for the current player.
    If action_idx is not legal (e.g. sampled randomly by RLlib env checks),
    the turn is silently advanced with zero reward.
    """
    action = asp.decode(action_idx)
    player = state.players[state.current_player]
    reward = 0.0

    atype = action.action_type

    if atype == ActionType.DRAW_FACE_UP:
        reward = _do_draw_face_up(state, action.slot, rng, second=False)

    elif atype == ActionType.DRAW_DECK:
        # Draw 2 cards from deck (whole turn)
        for _ in range(2):
            card = draw_card_from_deck(state, rng)
            if card:
                player.add_card(card)
        _advance_turn(state)

    elif atype == ActionType.DRAW_TICKETS:
        deal = TURN_TICKET_DEAL_BIG_CITIES if state.expansion == EXPANSION_BIG_CITIES else TURN_TICKET_DEAL
        count = min(deal, len(state.ticket_deck))
        state.pending_tickets = [state.ticket_deck.pop() for _ in range(count)]
        state.phase = GamePhase.TICKET_SELECTION

    elif atype == ActionType.DRAW_FACE_UP_SECOND:
        _do_draw_face_up(state, action.slot, rng, second=True)
        _advance_turn(state)

    elif atype == ActionType.DRAW_DECK_SECOND:
        card = draw_card_from_deck(state, rng)
        if card:
            player.add_card(card)
        _advance_turn(state)

    elif atype in (ActionType.KEEP_TICKETS, ActionType.KEEP_INIT_TICKETS):
        try:
            reward = _do_keep_tickets(state, action.slot)
        except (ValueError, IndexError):
            _advance_turn(state)

    elif atype == ActionType.CLAIM_ROUTE:
        try:
            reward = _do_claim_route(state, asp, action, rng)
        except (ValueError, IndexError):
            # Illegal action (e.g. sampled randomly during RLlib env checks)
            _advance_turn(state)

    elif atype == ActionType.PLACE_STATION:
        try:
            _do_place_station(state, asp, action)
        except (ValueError, IndexError):
            # Illegal action (e.g. sampled randomly during RLlib env checks)
            pass
        _advance_turn(state)

    elif atype == ActionType.TUNNEL_PAY:
        reward = _do_tunnel_resolve(state, asp, pay=True)

    elif atype == ActionType.TUNNEL_DECLINE:
        _do_tunnel_resolve(state, asp, pay=False)

    return reward


def _do_draw_face_up(state: GameState, slot: int, rng: random.Random,
                     second: bool) -> float:
    player = state.players[state.current_player]
    card = state.face_up[slot]
    player.add_card(card)
    replenish_face_up(state, slot, rng)

    if not second:
        if card == LOCO:
            # Drawing a face-up locomotive ends the turn
            state.first_draw_was_loco = True
            _advance_turn(state)
        else:
            state.first_draw_was_loco = False
            state.phase = GamePhase.SECOND_DRAW
    return 0.0


def _do_keep_tickets(state: GameState, mask: int) -> float:
    player = state.players[state.current_player]

    # Mega Europe phase 1: choose 0 or 1 long route, then deal 5 regular tickets
    if state.phase == GamePhase.MEGA_LONG_SELECTION:
        for i, ticket in enumerate(state.pending_tickets):
            if mask & (1 << i):
                player.tickets.append(ticket)
                state.mega_long_kept = True
        # Unkept long tickets are removed from the game (not returned to deck)
        state.pending_tickets = []
        # Deal 5 regular tickets for the INITIAL_TICKET_SELECTION phase
        count = min(5, len(state.ticket_deck))
        state.pending_tickets = [state.ticket_deck.pop() for _ in range(count)]
        state.phase = GamePhase.INITIAL_TICKET_SELECTION
        return 0.0

    kept = []
    discarded = []
    for i, ticket in enumerate(state.pending_tickets):
        if mask & (1 << i):
            kept.append(ticket)
        else:
            discarded.append(ticket)
    player.tickets.extend(kept)
    state.pending_tickets = []

    if state.phase == GamePhase.INITIAL_TICKET_SELECTION:
        # Initial discards leave the game (go back in the box) — NOT back in the deck
        state.init_tickets_done += 1
        if state.init_tickets_done < len(state.players):
            # Move to next player's initial selection
            state.current_player = state.init_tickets_done
            state.mega_long_kept = False  # reset for next player
            if state.expansion == EXPANSION_MEGA:
                # Next player gets 2 long tickets first (MEGA_LONG_SELECTION)
                pending = [state.long_ticket_deck.pop()
                           for _ in range(min(2, len(state.long_ticket_deck)))]
                state.pending_tickets = pending
                state.phase = GamePhase.MEGA_LONG_SELECTION
            elif state.expansion == EXPANSION_BIG_CITIES:
                # Big Cities: deal 5 big-city regular tickets (no long routes)
                count = min(5, len(state.ticket_deck))
                state.pending_tickets = [state.ticket_deck.pop() for _ in range(count)]
                # phase stays INITIAL_TICKET_SELECTION
            else:
                # Base / 1912 / Europe Expanded: 1 long + 3 regular
                pending = []
                if state.long_ticket_deck:
                    pending.append(state.long_ticket_deck.pop())
                for _ in range(min(INITIAL_TICKET_REGULAR_DEAL, len(state.ticket_deck))):
                    pending.append(state.ticket_deck.pop())
                state.pending_tickets = pending
        else:
            # All players done; start the main game
            state.current_player = 0
            state.phase = GamePhase.MAIN_TURN
    else:
        # Turn draws: discarded tickets return to the bottom of the ticket deck
        state.ticket_deck = discarded + state.ticket_deck
        _advance_turn(state)
    return 0.0


def _do_claim_route(state: GameState, asp: ActionSpace,
                    action: Action, rng: random.Random) -> float:
    player = state.players[state.current_player]
    route_idx = action.slot
    route = state.board.routes[route_idx]
    color = action.color
    ferries = route.ferries
    remaining = route.length - ferries
    loco_in_hand = player.hand.get(LOCO, 0)

    # Determine card split
    color_count = player.hand.get(color, 0)
    locos_for_color = max(0, remaining - color_count)

    # Pay ferry locomotives
    ferry_locos_paid = ferries
    player.hand[LOCO] = loco_in_hand - ferries
    # Pay remaining cards (color + any locos for gaps)
    color_paid = min(remaining, color_count)
    loco_color_paid = remaining - color_paid
    player.pay_cards(color, remaining, locos_used=loco_color_paid)

    # Cards paid so far go to discard
    discard_cards = [color] * color_paid + [LOCO] * (ferry_locos_paid + loco_color_paid)

    # Tunnel resolution: draw 3 cards and calculate extra cost
    extra = 0
    if route.tunnel:
        tunnel_cards = []
        for _ in range(3):
            c = draw_card_from_deck(state, rng)
            if c is not None:
                tunnel_cards.append(c)
        # Count matching cards (same color or loco)
        extra = sum(1 for c in tunnel_cards if c == color or c == LOCO)
        # Tunnel reveal cards always return to discard
        state.discard.extend(tunnel_cards)

        if extra > 0:
            current_color = player.hand.get(color, 0)
            current_loco = player.hand.get(LOCO, 0)
            if current_color + current_loco < extra:
                # Cannot pay — return all paid cards to hand and abort
                _refund_route_payment(player, color, color_paid, loco_color_paid, ferry_locos_paid)
                _advance_turn(state)
                return 0.0
            if state.interactive_tunnels:
                # Pause: let the human player decide whether to pay the extra cost.
                # Base payment cards have already been deducted; store them for later.
                state.tunnel_route_idx = route_idx
                state.tunnel_color_idx = action.color_idx
                state.tunnel_cards = list(tunnel_cards)
                state.tunnel_extra_cost = extra
                state.tunnel_color_paid = color_paid
                state.tunnel_loco_color_paid = loco_color_paid
                state.tunnel_ferry_locos_paid = ferry_locos_paid
                state.phase = GamePhase.TUNNEL_RESOLUTION
                return 0.0
            # RL auto-resolve: pay extra immediately
            extra_color = min(extra, current_color)
            extra_loco = extra - extra_color
            player.pay_cards(color, extra, locos_used=extra_loco)
            discard_cards += [color] * extra_color + [LOCO] * extra_loco

    # Send paid cards to discard
    state.discard.extend(discard_cards)

    # Claim the route
    state.claimed_routes[route_idx] = state.current_player
    player.trains -= route.length
    points = TRAIN_SCORING.get(route.length, 0)
    player.score += points

    # Check if final round should start
    if (player.trains <= FINAL_ROUND_TRIGGER
            and state.final_round_starter is None):
        state.final_round_starter = state.current_player

    _advance_turn(state)
    return float(points)


def _refund_route_payment(player: PlayerState, color: str, color_paid: int,
                           loco_color_paid: int, ferry_locos_paid: int) -> None:
    """Return cards to player's hand after a failed tunnel claim."""
    player.hand[color] = player.hand.get(color, 0) + color_paid
    player.hand[LOCO] = player.hand.get(LOCO, 0) + loco_color_paid + ferry_locos_paid


def _do_tunnel_resolve(state: GameState, asp: ActionSpace, pay: bool) -> float:
    """Complete or cancel a paused TUNNEL_RESOLUTION claim."""
    player = state.players[state.current_player]
    route_idx = state.tunnel_route_idx
    color_idx = state.tunnel_color_idx
    color = COLORS[color_idx] if color_idx < len(COLORS) else LOCO
    color_paid = state.tunnel_color_paid
    loco_color_paid = state.tunnel_loco_color_paid
    ferry_locos_paid = state.tunnel_ferry_locos_paid
    extra = state.tunnel_extra_cost

    # Reconstruct the base discard list (cards already taken from hand)
    base_discard = [color] * color_paid + [LOCO] * (ferry_locos_paid + loco_color_paid)

    # Clear tunnel state
    state.tunnel_route_idx = None
    state.tunnel_color_idx = 0
    state.tunnel_cards = []
    state.tunnel_extra_cost = 0
    state.tunnel_color_paid = 0
    state.tunnel_loco_color_paid = 0
    state.tunnel_ferry_locos_paid = 0

    if not pay:
        # Refund base payment and abandon
        _refund_route_payment(player, color, color_paid, loco_color_paid, ferry_locos_paid)
        _advance_turn(state)
        return 0.0

    # Pay extra cards and complete the claim
    current_color = player.hand.get(color, 0)
    extra_color = min(extra, current_color)
    extra_loco = extra - extra_color
    player.pay_cards(color, extra, locos_used=extra_loco)
    all_discard = base_discard + [color] * extra_color + [LOCO] * extra_loco
    state.discard.extend(all_discard)

    route = state.board.routes[route_idx]
    state.claimed_routes[route_idx] = state.current_player
    player.trains -= route.length
    points = TRAIN_SCORING.get(route.length, 0)
    player.score += points

    if (player.trains <= FINAL_ROUND_TRIGGER and state.final_round_starter is None):
        state.final_round_starter = state.current_player

    _advance_turn(state)
    return float(points)


def _do_place_station(state: GameState, asp: ActionSpace, action: Action) -> None:
    player = state.players[state.current_player]
    city = state.board.cities[action.slot]
    color = action.color  # may be LOCO
    station_num = NUM_STATIONS - player.stations
    cost = STATION_COSTS[station_num]
    player.hand[color] = player.hand.get(color, 0) - cost
    player.stations -= 1
    player.station_cities.append(city)
    state.discard.extend([color] * cost)


def _advance_turn(state: GameState) -> None:
    """Move to the next player's turn, or end the game if the final round is complete."""
    num_players = len(state.players)
    next_player = (state.current_player + 1) % num_players
    state.current_player = next_player

    if state.final_round_starter is not None:
        if next_player == state.final_round_starter:
            state.phase = GamePhase.GAME_OVER
        else:
            state.phase = GamePhase.FINAL_ROUND
    else:
        state.phase = GamePhase.MAIN_TURN


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def final_score_breakdown(state: GameState) -> List[dict]:
    """
    Return a per-player breakdown of how the final score is composed:
      route_score         — points earned from claimed routes
      unused_stations     — number of station tokens not placed
      station_bonus       — unused_stations × 4
      tickets             — list of {city1, city2, points, completed}
      ticket_total        — net ticket points (+completed, -failed)
      longest_route_length— length of each player's longest continuous path
      longest_route_bonus — LONGEST_ROUTE_BONUS if this player holds the record
      total               — final score
    """
    lengths = [_longest_route(p, state) for p in state.players]
    max_length = max(lengths) if lengths else 0

    breakdowns = []
    for i, player in enumerate(state.players):
        station_bonus = player.stations * 4

        player_routes = _player_route_set(player, state)
        borrowed = _optimal_station_routes(player, state, player_routes)
        all_routes = player_routes | borrowed

        ticket_results = []
        ticket_total = 0
        for ticket in player.tickets:
            completed = _cities_connected(ticket.city1, ticket.city2, all_routes, state.board)
            delta = ticket.points if completed else -ticket.points
            ticket_total += delta
            ticket_results.append({
                "city1": ticket.city1,
                "city2": ticket.city2,
                "points": ticket.points,
                "completed": completed,
            })

        longest_bonus = LONGEST_ROUTE_BONUS if (max_length >= 1 and lengths[i] == max_length) else 0

        breakdowns.append({
            "route_score": player.score,
            "unused_stations": player.stations,
            "station_bonus": station_bonus,
            "tickets": ticket_results,
            "ticket_total": ticket_total,
            "longest_route_length": lengths[i],
            "longest_route_bonus": longest_bonus,
            "total": player.score + station_bonus + ticket_total + longest_bonus,
        })

    return breakdowns


def final_scores(state: GameState) -> List[int]:
    """
    Compute final scores for all players:
      + route points (already in player.score)
      + destination ticket bonuses/penalties
      + longest route bonus (+10)
      + station bonus (+4 per unused station)

    Returns list of total scores indexed by player_id.
    """
    board = state.board
    num_players = len(state.players)
    scores = [p.score for p in state.players]

    # Station bonus: +4 per unused station token
    for i, player in enumerate(state.players):
        scores[i] += player.stations * 4

    # Destination tickets — compute optimal station assignment once per player
    for i, player in enumerate(state.players):
        player_routes = _player_route_set(player, state)
        borrowed = _optimal_station_routes(player, state, player_routes)
        all_routes = player_routes | borrowed
        for ticket in player.tickets:
            if _cities_connected(ticket.city1, ticket.city2, all_routes, state.board):
                scores[i] += ticket.points
            else:
                scores[i] -= ticket.points

    # Longest continuous route
    lengths = [_longest_route(player, state) for player in state.players]
    max_length = max(lengths)
    if max_length >= 1:
        for i, length in enumerate(lengths):
            if length == max_length:
                scores[i] += LONGEST_ROUTE_BONUS

    return scores


def _ticket_completed(ticket: DestinationTicket, player: PlayerState,
                       state: GameState) -> bool:
    """
    Return True if `player` has a connected path between ticket.city1 and ticket.city2
    using their own claimed routes plus the optimal assignment of station borrows.
    Used for mid-game display; final scoring calls _optimal_station_routes directly.
    """
    player_routes = _player_route_set(player, state)
    borrowed = _optimal_station_routes(player, state, player_routes)
    return _cities_connected(ticket.city1, ticket.city2, player_routes | borrowed, state.board)


def player_ticket_completions(state: GameState, player_idx: int) -> List[bool]:
    """Return a per-ticket completion flag list for mid-game display."""
    player = state.players[player_idx]
    player_routes = _player_route_set(player, state)
    borrowed = _optimal_station_routes(player, state, player_routes)
    all_routes = player_routes | borrowed
    return [
        _cities_connected(t.city1, t.city2, all_routes, state.board)
        for t in player.tickets
    ]


def _player_route_set(player: PlayerState, state: GameState) -> Set[int]:
    """Return set of route indices claimed by this player."""
    return {idx for idx, pid in state.claimed_routes.items() if pid == player.player_id}


def _optimal_station_routes(player: PlayerState, state: GameState,
                             player_routes: Set[int]) -> Set[int]:
    """
    Choose at most one opponent-claimed route per station city to borrow,
    maximising the ticket points recovered from tickets not yet completable
    with the player's own routes alone.

    Search space: product(candidate_routes_per_station) — at most ~6^3 = 216
    combinations with 3 stations, so brute-force is fine.
    """
    if not player.station_cities:
        return set()

    board = state.board
    # Build a fast seg→index lookup to avoid O(n) list.index() calls
    route_index: Dict = {seg: i for i, seg in enumerate(board.routes)}

    # For each station city collect the opponent-claimed routes adjacent to it
    station_candidates: List[List[int]] = []
    for city in player.station_cities:
        cands: List[int] = []
        for seg in board.adj.get(city, []):
            idx = route_index.get(seg)
            if idx is None:
                continue
            owner = state.claimed_routes.get(idx)
            if owner is not None and owner != player.player_id:
                cands.append(idx)
        station_candidates.append(cands)

    # Only consider tickets that are currently failing (stations can't help the rest)
    failed_tickets = [
        t for t in player.tickets
        if not _cities_connected(t.city1, t.city2, player_routes, board)
    ]
    if not failed_tickets:
        return set()

    # Try every combination: borrow one route per station, or skip that station
    best_points = 0
    best_borrowed: Set[int] = set()
    for combo in itertools.product(*[[None] + cands for cands in station_candidates]):
        borrowed = {r for r in combo if r is not None}
        all_routes = player_routes | borrowed
        points = sum(
            t.points for t in failed_tickets
            if _cities_connected(t.city1, t.city2, all_routes, board)
        )
        if points > best_points:
            best_points = points
            best_borrowed = borrowed

    return best_borrowed


def _cities_connected(city1: str, city2: str, route_set: Set[int],
                       board: Board) -> bool:
    """BFS/DFS to check connectivity between city1 and city2 using only routes in route_set."""
    if city1 == city2:
        return True
    visited: Set[str] = set()
    stack = [city1]
    while stack:
        current = stack.pop()
        if current == city2:
            return True
        if current in visited:
            continue
        visited.add(current)
        for seg in board.adj.get(current, []):
            route_idx = board.routes.index(seg)
            if route_idx not in route_set:
                continue
            neighbor = seg.city2 if seg.city1 == current else seg.city1
            if neighbor not in visited:
                stack.append(neighbor)
    return False


def _longest_route(player: PlayerState, state: GameState) -> int:
    """
    Find the length of the longest continuous route path for this player.
    Uses DFS with backtracking to count maximum connected train-car path.
    """
    player_routes = _player_route_set(player, state)
    if not player_routes:
        return 0

    board = state.board
    # Build adjacency for this player's claimed routes
    adj: Dict[str, List[Tuple[str, int, int]]] = {}  # city → [(neighbor, length, route_idx)]
    for route_idx in player_routes:
        seg = board.routes[route_idx]
        adj.setdefault(seg.city1, []).append((seg.city2, seg.length, route_idx))
        adj.setdefault(seg.city2, []).append((seg.city1, seg.length, route_idx))

    best = [0]

    def dfs(city: str, used_routes: Set[int], current_length: int) -> None:
        best[0] = max(best[0], current_length)
        for neighbor, length, route_idx in adj.get(city, []):
            if route_idx not in used_routes:
                used_routes.add(route_idx)
                dfs(neighbor, used_routes, current_length + length)
                used_routes.remove(route_idx)

    for start_city in adj:
        dfs(start_city, set(), 0)

    return best[0]


def is_terminal(state: GameState) -> bool:
    return state.phase == GamePhase.GAME_OVER


# ---------------------------------------------------------------------------
# Convenience import for missing constant
# ---------------------------------------------------------------------------
from .info import NUM_STATIONS
