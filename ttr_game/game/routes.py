"""
Destination tickets for Ticket to Ride: Europe and its expansions.

Edition flags on each ticket:
  in_base       — original TTR Europe (6 long + 40 regular = 46 total)
  in_1912       — TTR Europe 1912 expansion
                  Long tickets: replace the 6 base long tickets with 6 new ones
                  Regular tickets: base regular + 1912 regular (combined deck)
  in_big_cities — Big Cities expansion
                  Uses the 15 Big-Cities-marked base tickets + 30 new shared tickets

Helper:
  get_ticket_set(expansion) → (long_tickets, regular_tickets)

Constants:
  TICKETS       — base game tickets (46), used as the observation universe in RL
  ALL_TICKETS   — every ticket across all editions (101 total)
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple

EXPANSION_BASE             = "base"
EXPANSION_1912             = "1912"
EXPANSION_EUROPE_EXPANDED  = "europe_expanded"  # base 46 + 19 new 1912-only regular = 65
EXPANSION_BIG_CITIES       = "big_cities"        # Big Cities tickets only, no long routes
EXPANSION_MEGA             = "mega"              # all 12 long + all 89 regular


@dataclass(frozen=True)
class DestinationTicket:
    city1: str
    city2: str
    points: int
    is_long: bool
    in_base: bool = True
    in_1912: bool = False
    in_big_cities: bool = False

    def involves(self, city: str) -> bool:
        return city == self.city1 or city == self.city2

    def __str__(self) -> str:
        marker = "★" if self.is_long else " "
        return f"{marker} {self.city1}↔{self.city2} ({self.points}pts)"


# ---------------------------------------------------------------------------
# Complete ticket list — all editions
# ---------------------------------------------------------------------------

ALL_TICKETS: List[DestinationTicket] = [
    # ------------------------------------------------------------------
    # LONG-ROUTE TICKETS — BASE GAME  (6)
    # ------------------------------------------------------------------
    DestinationTicket("Brest",       "Petrograd",      20, True),
    DestinationTicket("Cadiz",       "Stockholm",      21, True),
    DestinationTicket("Edinburgh",   "Athina",         21, True),
    DestinationTicket("Kobenhavn",   "Erzurum",        21, True),
    DestinationTicket("Lisboa",      "Danzig",         20, True),
    DestinationTicket("Palermo",     "Moskva",         20, True),

    # ------------------------------------------------------------------
    # LONG-ROUTE TICKETS — 1912 EXPANSION  (6, replace base long deck)
    # ------------------------------------------------------------------
    DestinationTicket("Amsterdam",   "Rostov",         19, True,  in_base=False, in_1912=True),
    DestinationTicket("Essen",       "Angora",         16, True,  in_base=False, in_1912=True),
    DestinationTicket("London",      "Sochi",          20, True,  in_base=False, in_1912=True),
    DestinationTicket("Pamplona",    "Kyiv",           18, True,  in_base=False, in_1912=True),
    DestinationTicket("Paris",       "Sevastopol",     17, True,  in_base=False, in_1912=True),
    DestinationTicket("Riga",        "Brindisi",       17, True,  in_base=False, in_1912=True),

    # ------------------------------------------------------------------
    # REGULAR TICKETS — BASE GAME only  (25)
    # ------------------------------------------------------------------
    DestinationTicket("Amsterdam",   "Pamplona",        7, False),
    DestinationTicket("Amsterdam",   "Wilno",          12, False),
    DestinationTicket("Barcelona",   "Bruxelles",       8, False),
    DestinationTicket("Barcelona",   "Munchen",         8, False),
    DestinationTicket("Brest",       "Marseille",       7, False),
    DestinationTicket("Brest",       "Venezia",         8, False),
    DestinationTicket("Bruxelles",   "Danzig",          9, False),
    DestinationTicket("Budapest",    "Sofia",           5, False),
    DestinationTicket("Essen",       "Kyiv",           10, False),
    DestinationTicket("Frankfurt",   "Kobenhavn",       5, False),
    DestinationTicket("Frankfurt",   "Smolensk",       13, False),
    DestinationTicket("Kyiv",        "Petrograd",       6, False),
    DestinationTicket("Kyiv",        "Sochi",           8, False),
    DestinationTicket("Marseille",   "Essen",           8, False),
    DestinationTicket("Palermo",     "Constantinople",  8, False),
    DestinationTicket("Riga",        "Bucuresti",      10, False),
    DestinationTicket("Rostov",      "Erzurum",         5, False),
    DestinationTicket("Sarajevo",    "Sevastopol",      8, False),
    DestinationTicket("Smolensk",    "Rostov",          8, False),
    DestinationTicket("Sofia",       "Smyrna",          5, False),
    DestinationTicket("Venezia",     "Constantinople", 10, False),
    DestinationTicket("Warszawa",    "Smolensk",        6, False),
    DestinationTicket("Zagrab",      "Brindisi",        6, False),
    DestinationTicket("Zurich",      "Brindisi",        6, False),
    DestinationTicket("Zurich",      "Budapest",        6, False),

    # ------------------------------------------------------------------
    # REGULAR TICKETS — BASE GAME, also in Big Cities expansion  (15)
    # ------------------------------------------------------------------
    DestinationTicket("Angora",      "Kharkov",        10, False, in_big_cities=True),
    DestinationTicket("Athina",      "Angora",          5, False, in_big_cities=True),
    DestinationTicket("Athina",      "Wilno",          11, False, in_big_cities=True),
    DestinationTicket("Berlin",      "Bucuresti",       8, False, in_big_cities=True),
    DestinationTicket("Berlin",      "Moskva",         12, False, in_big_cities=True),
    DestinationTicket("Berlin",      "Roma",            9, False, in_big_cities=True),
    DestinationTicket("Edinburgh",   "Paris",           7, False, in_big_cities=True),
    DestinationTicket("London",      "Berlin",          7, False, in_big_cities=True),
    DestinationTicket("London",      "Wien",           10, False, in_big_cities=True),
    DestinationTicket("Madrid",      "Dieppe",          8, False, in_big_cities=True),
    DestinationTicket("Madrid",      "Zurich",          8, False, in_big_cities=True),
    DestinationTicket("Paris",       "Wien",            8, False, in_big_cities=True),
    DestinationTicket("Paris",       "Zagrab",          7, False, in_big_cities=True),
    DestinationTicket("Roma",        "Smyrna",          8, False, in_big_cities=True),
    DestinationTicket("Stockholm",   "Wien",           11, False, in_big_cities=True),

    # ------------------------------------------------------------------
    # REGULAR TICKETS — 1912 EXPANSION only  (19)
    # ------------------------------------------------------------------
    DestinationTicket("Amsterdam",   "Venezia",         6, False, in_base=False, in_1912=True),
    DestinationTicket("Bucuresti",   "Erzurum",         7, False, in_base=False, in_1912=True),
    DestinationTicket("Bruxelles",   "Stockholm",      10, False, in_base=False, in_1912=True),
    DestinationTicket("Cadiz",       "Frankfurt",      13, False, in_base=False, in_1912=True),
    DestinationTicket("Danzig",      "Budapest",        7, False, in_base=False, in_1912=True),
    DestinationTicket("Dieppe",      "Kobenhavn",       9, False, in_base=False, in_1912=True),
    DestinationTicket("Dieppe",      "Marseille",       5, False, in_base=False, in_1912=True),
    DestinationTicket("Edinburgh",   "Essen",           9, False, in_base=False, in_1912=True),
    DestinationTicket("Lisboa",      "Cadiz",           2, False, in_base=False, in_1912=True),
    DestinationTicket("Munchen",     "Petrograd",      14, False, in_base=False, in_1912=True),
    DestinationTicket("Munchen",     "Sarajevo",        7, False, in_base=False, in_1912=True),
    DestinationTicket("Pamplona",    "Palermo",        12, False, in_base=False, in_1912=True),
    DestinationTicket("Riga",        "Kharkov",        10, False, in_base=False, in_1912=True),
    DestinationTicket("Sochi",       "Smyrna",          9, False, in_base=False, in_1912=True),
    DestinationTicket("Sofia",       "Kyiv",            6, False, in_base=False, in_1912=True),
    DestinationTicket("Stockholm",   "Wilno",          12, False, in_base=False, in_1912=True),
    DestinationTicket("Venezia",     "Warszawa",        8, False, in_base=False, in_1912=True),
    DestinationTicket("Warszawa",    "Budapest",        5, False, in_base=False, in_1912=True),
    DestinationTicket("Warszawa",    "Sevastopol",     12, False, in_base=False, in_1912=True),

    # ------------------------------------------------------------------
    # REGULAR TICKETS — in BOTH 1912 and Big Cities expansions  (30)
    # ------------------------------------------------------------------
    DestinationTicket("Berlin",      "Angora",         13, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Berlin",      "Athina",         11, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Berlin",      "Wien",            3, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("London",      "Angora",         20, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("London",      "Athina",         16, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("London",      "Madrid",         10, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("London",      "Moskva",         19, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("London",      "Paris",           3, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("London",      "Roma",           10, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Madrid",      "Angora",         21, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Madrid",      "Athina",         16, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Madrid",      "Berlin",         13, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Madrid",      "Moskva",         25, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Madrid",      "Roma",           10, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Madrid",      "Wien",           13, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Moskva",      "Angora",         14, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Moskva",      "Athina",         14, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Paris",       "Angora",         13, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Paris",       "Athina",         13, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Paris",       "Berlin",          7, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Paris",       "Madrid",          7, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Paris",       "Moskva",         18, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Paris",       "Roma",           10, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Roma",        "Angora",         11, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Roma",        "Athina",          6, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Roma",        "Moskva",         17, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Wien",        "Angora",         10, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Wien",        "Athina",          8, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Wien",        "Moskva",         12, False, in_base=False, in_1912=True, in_big_cities=True),
    DestinationTicket("Wien",        "Roma",            6, False, in_base=False, in_1912=True, in_big_cities=True),
]

# Base game tickets (46: 6 long + 40 regular) — used as the RL observation universe
TICKETS: List[DestinationTicket] = [t for t in ALL_TICKETS if t.in_base]


# ---------------------------------------------------------------------------
# Expansion ticket sets
# ---------------------------------------------------------------------------

def get_ticket_set(expansion: str = EXPANSION_BASE) -> Tuple[List[DestinationTicket], List[DestinationTicket]]:
    """
    Return (long_tickets, regular_tickets) for the given expansion.

    "base"             — original TTR Europe: 6 long + 40 regular (46 total)
    "1912"             — TTR Europe 1912: 6 new long + base40 + 1912-49 regular (95 total)
    "europe_expanded"  — base 46 + 19 new 1912-only regular = 6 long + 59 regular (65 total)
    "big_cities"       — Big Cities: no long routes + 45 big-city regular (45 total)
    "mega"             — Mega Europe: all 12 long + all 89 regular (101 total)
    """
    if expansion == EXPANSION_1912:
        long_tickets    = [t for t in ALL_TICKETS if t.is_long and t.in_1912]
        regular_tickets = [t for t in ALL_TICKETS if not t.is_long and (t.in_base or t.in_1912)]
    elif expansion == EXPANSION_EUROPE_EXPANDED:
        long_tickets    = [t for t in ALL_TICKETS if t.is_long and t.in_base]
        # Base 40 regular + 19 that are 1912-only (not in big_cities)
        regular_tickets = [t for t in ALL_TICKETS
                           if not t.is_long and (t.in_base or (t.in_1912 and not t.in_big_cities))]
    elif expansion == EXPANSION_BIG_CITIES:
        long_tickets    = []  # long routes are not used in Big Cities
        regular_tickets = [t for t in ALL_TICKETS if not t.is_long and t.in_big_cities]
    elif expansion == EXPANSION_MEGA:
        long_tickets    = [t for t in ALL_TICKETS if t.is_long]  # all 12
        regular_tickets = [t for t in ALL_TICKETS if not t.is_long and (t.in_base or t.in_1912)]
    else:  # base
        long_tickets    = [t for t in ALL_TICKETS if t.is_long and t.in_base]
        regular_tickets = [t for t in ALL_TICKETS if not t.is_long and t.in_base]
    return long_tickets, regular_tickets


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def tickets_involving(city: str) -> List[DestinationTicket]:
    """Return all base-game tickets that start or end at the given city."""
    return [t for t in TICKETS if t.involves(city)]


def find_ticket(city1: str, city2: str) -> Optional[DestinationTicket]:
    """Return the base-game ticket between two cities, or None if not found."""
    for t in TICKETS:
        if {t.city1, t.city2} == {city1, city2}:
            return t
    return None
