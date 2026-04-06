"""
Board graph for Ticket to Ride: Europe.

Each claimable route between two cities is represented as a RouteSegment.
Double routes (two parallel routes between the same city pair) become two
separate RouteSegment objects, each with a different `parallel_index`.

Edge tuple from C++ source: (length, dest, ferries, color, tunnel, is_double)
  - color: single letter = one route; two letters = double route (split here)
  - "X" = gray (any color); "XX" = double-gray
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class RouteSegment:
    """A single claimable route between two cities (canonical: city1 < city2 alphabetically)."""
    city1: str
    city2: str
    length: int
    color: str          # one of COLORS or "X" (gray)
    ferries: int        # number of locomotive cards that must be paid as ferries
    tunnel: bool        # if True, extra cards may be required when claiming
    parallel_index: int = 0  # 0 or 1 for double routes

    def cities(self) -> Tuple[str, str]:
        return (self.city1, self.city2)

    def __str__(self) -> str:
        suffix = f" [{self.parallel_index}]" if self.parallel_index else ""
        extras = []
        if self.tunnel:
            extras.append("tunnel")
        if self.ferries:
            extras.append(f"ferry×{self.ferries}")
        extra_str = f" ({', '.join(extras)})" if extras else ""
        return f"{self.city1}↔{self.city2} len={self.length} {self.color}{suffix}{extra_str}"


class Board:
    """
    Europe map as a graph.  Access routes via `self.routes` (list of all
    RouteSegments, indexed) and `self.adj` (adjacency list for pathfinding).
    """

    def __init__(self) -> None:
        # All claimable route segments, indexed — index is the canonical route ID
        self.routes: List[RouteSegment] = []
        # Adjacency list: city → list of RouteSegments leaving that city
        self.adj: Dict[str, List[RouteSegment]] = {}
        # All city names
        self.cities: List[str] = []
        self._build()
        self._finalize()

    # ------------------------------------------------------------------
    # Internal construction helpers
    # ------------------------------------------------------------------

    def _add(self, c1: str, length: int, c2: str, ferries: int,
             color: str, tunnel: bool, is_double: bool) -> None:
        """
        Add one or two route segments from the raw edge data.

        Two-letter color codes encode double routes:
          "KW" → one Black route + one White route (parallel_index 0 and 1)
          "XX" → two Gray routes
        """
        canonical_c1 = min(c1, c2)
        canonical_c2 = max(c1, c2)

        if is_double:
            if color == "XX":
                colors = ["X", "X"]
            else:
                colors = [color[0], color[1]]
            for idx, col in enumerate(colors):
                seg = RouteSegment(canonical_c1, canonical_c2, length,
                                   col, ferries, tunnel, parallel_index=idx)
                if seg not in self.routes:
                    self.routes.append(seg)
            # Add both to adjacency list (each direction, each parallel)
            for col in colors:
                seg_fwd = RouteSegment(canonical_c1, canonical_c2, length, col, ferries, tunnel,
                                       parallel_index=colors.index(col))
                self.adj.setdefault(c1, [])
                self.adj.setdefault(c2, [])
        else:
            seg = RouteSegment(canonical_c1, canonical_c2, length,
                               color, ferries, tunnel, parallel_index=0)
            if seg not in self.routes:
                self.routes.append(seg)

        # Always register both cities in adjacency
        self.adj.setdefault(c1, [])
        self.adj.setdefault(c2, [])

    def _finalize(self) -> None:
        """Build adjacency list from route list and collect city names."""
        for route in self.routes:
            self.adj.setdefault(route.city1, []).append(route)
            self.adj.setdefault(route.city2, []).append(route)
        self.cities = sorted(self.adj.keys())

    def neighbors(self, city: str) -> List[str]:
        """Return cities directly connected to `city`."""
        seen = set()
        result = []
        for seg in self.adj.get(city, []):
            neighbor = seg.city2 if seg.city1 == city else seg.city1
            if neighbor not in seen:
                seen.add(neighbor)
                result.append(neighbor)
        return result

    def routes_between(self, city1: str, city2: str) -> List[RouteSegment]:
        """Return all route segments between two cities (1 or 2 for double routes)."""
        c1, c2 = min(city1, city2), max(city1, city2)
        return [r for r in self.routes if r.city1 == c1 and r.city2 == c2]

    def route_by_index(self, idx: int) -> RouteSegment:
        return self.routes[idx]

    # ------------------------------------------------------------------
    # Board data (ported from Board.cpp, typos corrected)
    # ------------------------------------------------------------------

    def _build(self) -> None:
        # _add(city1, length, city2, ferries, color, tunnel, is_double)
        # Iberian peninsula
        self._add("Cadiz",    3, "Madrid",    0, "O",  False, False)
        self._add("Cadiz",    2, "Lisboa",    0, "B",  False, False)
        self._add("Lisboa",   3, "Madrid",    0, "P",  False, False)
        self._add("Madrid",   2, "Barcelona", 0, "Y",  False, False)  # fixed: was "Bacelona"
        self._add("Madrid",   3, "Pamplona",  0, "KW", True,  True)
        self._add("Barcelona",2, "Pamplona",  0, "X",  True,  False)
        self._add("Barcelona",4, "Marseille", 0, "X",  False, False)
        self._add("Pamplona", 4, "Brest",     0, "P",  False, False)
        self._add("Pamplona", 4, "Paris",     0, "GB", False, True)
        self._add("Pamplona", 4, "Marseille", 0, "R",  False, False)
        # France
        self._add("Marseille",4, "Paris",     0, "X",  False, False)
        self._add("Marseille",2, "Zurich",    0, "P",  True,  False)
        self._add("Marseille",4, "Roma",      0, "X",  True,  False)
        self._add("Brest",    3, "Paris",     0, "K",  False, False)
        self._add("Brest",    2, "Dieppe",    0, "O",  False, False)
        self._add("Paris",    3, "Zurich",    0, "X",  True,  False)
        self._add("Paris",    3, "Frankfurt", 0, "WO", False, True)
        self._add("Paris",    2, "Bruxelles", 0, "YR", False, True)
        self._add("Paris",    1, "Dieppe",    0, "P",  False, False)
        self._add("Dieppe",   2, "London",    1, "XX", False, True)
        self._add("Dieppe",   2, "Bruxelles", 0, "G",  False, False)
        # British Isles
        self._add("London",   2, "Amsterdam", 2, "X",  False, False)
        self._add("London",   4, "Edinburgh", 0, "OK", False, True)
        # Benelux / Germany
        self._add("Amsterdam",3, "Essen",     0, "Y",  False, False)
        self._add("Amsterdam",2, "Frankfurt", 0, "W",  False, False)
        self._add("Amsterdam",1, "Bruxelles", 0, "K",  False, False)
        self._add("Bruxelles",2, "Frankfurt", 0, "B",  False, False)
        self._add("Frankfurt",2, "Essen",     0, "G",  False, False)
        self._add("Frankfurt",3, "Berlin",    0, "RK", False, True)
        self._add("Frankfurt",2, "Munchen",   0, "P",  False, False)
        self._add("Essen",    2, "Berlin",    0, "B",  False, False)
        self._add("Essen",    3, "Kobenhavn", 1, "XX", False, True)
        # Scandinavia
        self._add("Kobenhavn",3, "Stockholm", 0, "WY", False, True)
        self._add("Stockholm",8, "Petrograd", 0, "X",  True,  False)
        # Central Europe
        self._add("Berlin",   3, "Wien",      0, "G",  False, False)
        self._add("Berlin",   4, "Warszawa",  0, "PY", False, True)
        self._add("Berlin",   4, "Danzig",    0, "X",  False, False)
        self._add("Munchen",  3, "Wien",      0, "O",  False, False)
        self._add("Munchen",  2, "Zurich",    0, "Y",  True,  False)
        self._add("Munchen",  2, "Venezia",   0, "B",  True,  False)
        self._add("Zurich",   2, "Venezia",   0, "G",  True,  False)
        # Italy
        self._add("Venezia",  2, "Zagrab",    0, "X",  False, False)
        self._add("Venezia",  2, "Roma",      0, "K",  False, False)
        self._add("Roma",     2, "Brindisi",  0, "W",  False, False)
        self._add("Roma",     4, "Palermo",   1, "X",  False, False)
        self._add("Palermo",  6, "Smyrna",    2, "X",  False, False)
        self._add("Palermo",  3, "Brindisi",  1, "X",  False, False)
        self._add("Brindisi", 4, "Athina",    1, "X",  False, False)
        # Balkans
        self._add("Zagrab",   3, "Sarajevo",  0, "R",  False, False)
        self._add("Zagrab",   2, "Budapest",  0, "O",  False, False)
        self._add("Zagrab",   2, "Wien",      0, "X",  False, False)
        self._add("Wien",     4, "Warszawa",  0, "B",  False, False)
        self._add("Wien",     1, "Budapest",  0, "WR", False, True)
        self._add("Budapest", 6, "Kyiv",      0, "X",  True,  False)
        self._add("Budapest", 4, "Bucuresti", 0, "X",  True,  False)
        self._add("Budapest", 3, "Sarajevo",  0, "P",  False, False)
        self._add("Sarajevo", 4, "Athina",    0, "G",  False, False)
        self._add("Sarajevo", 2, "Sofia",     0, "X",  True,  False)
        self._add("Sofia",    3, "Athina",    0, "P",  False, False)
        self._add("Sofia",    3, "Constantinople", 0, "B", False, False)
        self._add("Sofia",    2, "Bucuresti", 0, "X",  True,  False)
        self._add("Athina",   2, "Smyrna",    1, "X",  False, False)
        # Eastern Europe
        self._add("Petrograd",4, "Riga",      0, "X",  False, False)
        self._add("Petrograd",4, "Wilno",     0, "B",  False, False)
        self._add("Petrograd",4, "Moskva",    0, "W",  False, False)
        self._add("Danzig",   3, "Riga",      0, "K",  False, False)
        self._add("Danzig",   2, "Warszawa",  0, "X",  False, False)
        self._add("Warszawa", 4, "Kyiv",      0, "X",  False, False)
        self._add("Warszawa", 3, "Wilno",     0, "R",  False, False)
        self._add("Riga",     4, "Wilno",     0, "G",  False, False)
        self._add("Wilno",    3, "Smolensk",  0, "Y",  False, False)
        self._add("Wilno",    2, "Kyiv",      0, "X",  False, False)
        self._add("Moskva",   4, "Kharkov",   0, "X",  False, False)
        self._add("Moskva",   2, "Smolensk",  0, "O",  False, False)
        self._add("Smolensk", 3, "Kyiv",      0, "R",  False, False)
        self._add("Kyiv",     4, "Kharkov",   0, "X",  False, False)
        self._add("Kyiv",     4, "Bucuresti", 0, "X",  False, False)
        # Romania / Black Sea
        self._add("Bucuresti",4, "Sevastopol",0, "W",  False, False)
        self._add("Bucuresti",3, "Constantinople", 0, "Y", False, False)
        self._add("Constantinople", 4, "Sevastopol", 2, "X", False, False)
        self._add("Constantinople", 2, "Smyrna",    0, "X", True,  False)
        self._add("Constantinople", 2, "Angora",    0, "X", True,  False)
        # Turkey
        self._add("Smyrna",   3, "Angora",    0, "O",  True,  False)
        self._add("Angora",   3, "Erzurum",   0, "K",  False, False)
        self._add("Erzurum",  3, "Sochi",     0, "R",  True,  False)
        self._add("Erzurum",  4, "Sevastopol",2, "X",  False, False)
        self._add("Sevastopol",4,"Rostov",    0, "X",  False, False)
        self._add("Sevastopol",2,"Sochi",     1, "X",  False, False)
        self._add("Sochi",    2, "Rostov",    0, "X",  False, False)
        self._add("Rostov",   2, "Kharkov",   0, "G",  False, False)
