"""Game constants for Ticket to Ride: Europe."""

NUM_TRAINS = 45       # train cars per player
NUM_STATIONS = 3      # station tokens per player
NUM_DEST_TICKETS = 50 # total destination tickets
NUM_CARDS = 110       # total train cards in deck (8×12 + 14 locomotives)
LONGEST_ROUTE_BONUS = 10

# Points earned for claiming a route of N consecutive cars
TRAIN_SCORING: dict[int, int] = {
    1: 1,
    2: 2,
    3: 4,
    4: 7,
    5: 10,
    6: 15,
    7: 21,
    8: 21,
}

# Train card colors (single letter codes)
COLORS = ["P", "W", "B", "Y", "O", "K", "R", "G"]  # purple, white, blue, yellow, orange, black, red, green
LOCO = "L"   # locomotive (wild card)
GRAY = "X"   # gray route — any color accepted

# Number of each card type in the full deck
COLOR_CARD_COUNT: dict[str, int] = {
    "P": 12,
    "W": 12,
    "B": 12,
    "Y": 12,
    "O": 12,
    "K": 12,
    "R": 12,
    "G": 12,
    "L": 14,
}

# Color index mapping (for array-based observations)
COLOR_INDEX: dict[str, int] = {c: i for i, c in enumerate(COLORS)}

# Station cost in same-color cards for 1st, 2nd, 3rd station placed
STATION_COSTS = [1, 2, 3]

# Initial destination tickets: 1 long-route + 3 regular per player; keep ≥ 2
INITIAL_TICKET_LONG_DEAL = 1
INITIAL_TICKET_REGULAR_DEAL = 3
INITIAL_TICKET_MIN_KEEP = 2

# Destination tickets dealt on draw action (keep ≥ 1)
TURN_TICKET_DEAL = 3
TURN_TICKET_DEAL_BIG_CITIES = 4  # Big Cities draws 4, keeps ≥ 1

# Minimum trains remaining to trigger final round
FINAL_ROUND_TRIGGER = 2
