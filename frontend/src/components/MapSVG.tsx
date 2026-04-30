import { useMemo, useState } from "react";
import type { RouteInfo, PublicState, PrivateState, Ticket } from "../types";
import { PLAYER_COLORS, COLOR_HEX, COLORS, ACTION_CLAIM_ROUTE_START } from "../types";
import { CITY_COORDS } from "../data/cities";
import type { CityCoord } from "../data/cities";

const SVG_W = 1000;
const SVG_H = 650;
const SEG_H = 11;       // segment height (perpendicular to route)
const SEG_GAP = 3;      // gap between segments
const SEG_MARGIN = 8;   // clearance from city circles
const PARALLEL_OFFSET = 13; // px shift for parallel routes
const CLAIM_INSET = 3;  // px inset for claimed-route fill inside the outline

interface ColorPickerProps {
  routeIdx: number;
  legalActions: number[];
  onPick: (actionIdx: number) => void;
  onClose: () => void;
}

function ColorPicker({ routeIdx, legalActions, onPick, onClose }: ColorPickerProps) {
  const options: { colorIdx: number; label: string; hex: string; action: number }[] = [];
  for (let ci = 0; ci < 9; ci++) {
    const action = ACTION_CLAIM_ROUTE_START + routeIdx * 9 + ci;
    if (legalActions.includes(action)) {
      const colorCode = ci < 8 ? COLORS[ci] : "L";
      options.push({ colorIdx: ci, label: colorCode, hex: COLOR_HEX[colorCode], action });
    }
  }
  if (options.length === 0) return null;
  return (
    <div className="color-picker-overlay" onClick={onClose}>
      <div className="color-picker" onClick={e => e.stopPropagation()}>
        <p>Pay with which color?</p>
        {options.map(opt => (
          <button
            key={opt.colorIdx}
            className="color-pick-btn"
            style={{ background: opt.hex, color: opt.label === "W" ? "#111" : "#fff" }}
            onClick={() => { onPick(opt.action); onClose(); }}
          >
            {opt.label}
          </button>
        ))}
        <button className="btn-small" onClick={onClose}>Cancel</button>
      </div>
    </div>
  );
}

interface StationPickerProps {
  cityName: string;
  actions: number[];   // one per legal payment color
  onPick: (actionIdx: number) => void;
  onClose: () => void;
}

function StationPicker({ cityName, actions, onPick, onClose }: StationPickerProps) {
  // actions are PLACE_STATION_BASE + cityIdx*9 + colorIdx, so colorIdx = action % 9
  const options = actions.map(a => {
    const colorIdx = a % 9;
    const colorCode = colorIdx < 8 ? COLORS[colorIdx] : "L";
    return { colorIdx, label: colorCode, hex: COLOR_HEX[colorCode], action: a };
  });
  return (
    <div className="color-picker-overlay" onClick={onClose}>
      <div className="color-picker" onClick={e => e.stopPropagation()}>
        <p>Place station in <strong>{cityName}</strong></p>
        <p style={{ fontSize: 12, color: "#9CA3AF" }}>Pay with which color?</p>
        {options.map(opt => (
          <button
            key={opt.colorIdx}
            className="color-pick-btn"
            style={{ background: opt.hex, color: opt.label === "W" ? "#111" : "#fff" }}
            onClick={() => { onPick(opt.action); onClose(); }}
          >
            {opt.label}
          </button>
        ))}
        <button className="btn-small" onClick={onClose}>Cancel</button>
      </div>
    </div>
  );
}

interface Props {
  publicState: PublicState;
  privateState: PrivateState;
  isMyTurn: boolean;
  playerIdx: number;
  hoveredTicket: Ticket | null;
  onAction: (actionIdx: number) => void;
}

interface SegmentGeometry {
  segments: { cx: number; cy: number; w: number }[];
  angle: number;
  center: { x: number; y: number };
  hitPath: string;
}

function buildRouteGeometry(
  c1: CityCoord,
  c2: CityCoord,
  length: number,
  perpOffset: number,
): SegmentGeometry {
  const dx = c2.x - c1.x;
  const dy = c2.y - c1.y;
  const fullLen = Math.sqrt(dx * dx + dy * dy) || 1;
  const ux = dx / fullLen;
  const uy = dy / fullLen;
  const px = -uy; // perpendicular unit vector
  const py = ux;

  const ox = px * perpOffset;
  const oy = py * perpOffset;

  const availLen = fullLen - 2 * SEG_MARGIN;
  const segW = Math.max(6, (availLen - SEG_GAP * (length - 1)) / length);
  const angle = Math.atan2(dy, dx) * (180 / Math.PI);

  const segments: { cx: number; cy: number; w: number }[] = [];
  for (let i = 0; i < length; i++) {
    const t = SEG_MARGIN + i * (segW + SEG_GAP) + segW / 2;
    segments.push({ cx: c1.x + ux * t + ox, cy: c1.y + uy * t + oy, w: segW });
  }

  const midT = fullLen / 2;
  const center = { x: c1.x + ux * midT + ox, y: c1.y + uy * midT + oy };
  const hitPath = `M ${c1.x + ox} ${c1.y + oy} L ${c2.x + ox} ${c2.y + oy}`;

  return { segments, angle, center, hitPath };
}

export function MapSVG({ publicState, privateState, isMyTurn, playerIdx, hoveredTicket, onAction }: Props) {
  const [pickerRouteIdx, setPickerRouteIdx] = useState<number | null>(null);
  const [pickerStationCityIdx, setPickerStationCityIdx] = useState<number | null>(null);

  const claimedRoutes = publicState.claimed_routes;
  const legalActions = privateState.legal_actions;
  const routes = publicState.routes;
  const cities = publicState.cities ?? [];

  // First action index in the PLACE_STATION block (depends on board size)
  const PLACE_STATION_BASE = ACTION_CLAIM_ROUTE_START + routes.length * 9;

  const legalRouteSet = useMemo(() => {
    if (!isMyTurn) return new Set<number>();
    const s = new Set<number>();
    for (const a of legalActions) {
      if (a >= ACTION_CLAIM_ROUTE_START && a < PLACE_STATION_BASE) {
        const routeIdx = Math.floor((a - ACTION_CLAIM_ROUTE_START) / 9);
        if (routeIdx < routes.length) s.add(routeIdx);
      }
    }
    return s;
  }, [legalActions, isMyTurn, routes.length, PLACE_STATION_BASE]);

  // Map cityIdx → list of legal PLACE_STATION action indices for that city
  const stationCityActions = useMemo(() => {
    const map = new Map<number, number[]>();
    if (!isMyTurn) return map;
    const stationEnd = PLACE_STATION_BASE + cities.length * 9;
    for (const a of legalActions) {
      if (a >= PLACE_STATION_BASE && a < stationEnd) {
        const cityIdx = Math.floor((a - PLACE_STATION_BASE) / 9);
        if (!map.has(cityIdx)) map.set(cityIdx, []);
        map.get(cityIdx)!.push(a);
      }
    }
    return map;
  }, [legalActions, isMyTurn, PLACE_STATION_BASE, cities.length]);

  // Reverse lookup: city name → city index (using server-provided ordered list)
  const cityNameToIdx = useMemo(() => {
    const m = new Map<string, number>();
    cities.forEach((name, i) => m.set(name, i));
    return m;
  }, [cities]);

  // City pairs that have two parallel routes — used to center both around the midline
  const doubleRoutePairs = useMemo(() => {
    const pairs = new Set<string>();
    for (const r of routes) {
      if (r.parallel_index > 0) {
        pairs.add([r.city1, r.city2].sort().join("|"));
      }
    }
    return pairs;
  }, [routes]);

  // Cities featured in the player's current tickets
  const ticketCities = useMemo(() => {
    const s = new Set<string>();
    for (const t of privateState.tickets) { s.add(t.city1); s.add(t.city2); }
    return s;
  }, [privateState.tickets]);

  // Cities where the viewing player has placed a station
  const ownStationCities = useMemo(
    () => new Set(publicState.players[playerIdx]?.station_cities ?? []),
    [publicState.players, playerIdx],
  );

  // Cities where any other player has placed a station
  const otherStationCities = useMemo(() => {
    const s = new Set<string>();
    for (let i = 0; i < publicState.players.length; i++) {
      if (i !== playerIdx) {
        for (const city of publicState.players[i].station_cities) s.add(city);
      }
    }
    return s;
  }, [publicState.players, playerIdx]);

  // Priority: hover > own station > other station > ticket > default
  function cityFill(name: string): string {
    if (hoveredTicket && (hoveredTicket.city1 === name || hoveredTicket.city2 === name))
      return "#EF4444";
    if (ownStationCities.has(name)) return "#EF4444";
    if (otherStationCities.has(name)) return "#F97316";
    if (ticketCities.has(name)) return "#22C55E";
    return "#F9FAFB";
  }

  function handleRouteClick(route: RouteInfo) {
    if (!isMyTurn || !legalRouteSet.has(route.index)) return;
    const options: number[] = [];
    for (let ci = 0; ci < 9; ci++) {
      const a = ACTION_CLAIM_ROUTE_START + route.index * 9 + ci;
      if (legalActions.includes(a)) options.push(a);
    }
    if (options.length === 1) {
      onAction(options[0]);
    } else {
      setPickerRouteIdx(route.index);
    }
  }

  function handleCityClick(cityName: string) {
    if (!isMyTurn) return;
    const cityIdx = cityNameToIdx.get(cityName);
    if (cityIdx === undefined) return;
    const acts = stationCityActions.get(cityIdx);
    if (!acts || acts.length === 0) return;
    if (acts.length === 1) {
      onAction(acts[0]);
    } else {
      setPickerStationCityIdx(cityIdx);
    }
  }

  function segmentFill(route: RouteInfo): string {
    const claimedBy = claimedRoutes[String(route.index)];
    if (claimedBy !== undefined) return PLAYER_COLORS[claimedBy];
    if (route.color === "X") return "#9CA3AF";
    return COLOR_HEX[route.color] ?? "#9CA3AF";
  }

  function segmentFillOpacity(route: RouteInfo): number {
    if (claimedRoutes[String(route.index)] !== undefined) return 1;
    if (isMyTurn && legalRouteSet.has(route.index)) return 1;
    return 0.5;
  }

  return (
    <div className="map-container">
      <svg
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        className="map-svg"
        style={{ width: "100%", height: "100%" }}
      >
        {/* Background map image */}
        <image href="/TTR_map_v1.png" x={0} y={0} width={SVG_W} height={SVG_H} preserveAspectRatio="xMidYMid slice" />

        {/* Routes */}
        {routes.map(route => {
          const c1 = CITY_COORDS[route.city1];
          const c2 = CITY_COORDS[route.city2];
          if (!c1 || !c2) return null;

          const pairKey = [route.city1, route.city2].sort().join("|");
          const isDouble = doubleRoutePairs.has(pairKey);
          const HALF = PARALLEL_OFFSET / 2;
          const perpOffset = isDouble
            ? (route.parallel_index === 0 ? -HALF : HALF)
            : 0;
          const { segments, angle, center, hitPath } = buildRouteGeometry(
            c1, c2, route.length, perpOffset,
          );
          const fill = segmentFill(route);
          const fillOpacity = segmentFillOpacity(route);
          const claimed = claimedRoutes[String(route.index)] !== undefined;
          const legal = isMyTurn && legalRouteSet.has(route.index);
          const tickExt = SEG_H / 2 + 3;

          // Which segment indices carry a ferry anchor (evenly distributed)
          const ferrySegIndices = new Set(
            Array.from({ length: route.ferries }, (_, fi) =>
              Math.floor(segments.length * (2 * fi + 1) / (2 * route.ferries))
            )
          );

          return (
            <g key={route.index}>
              {/* Segment rectangles */}
              {segments.map((seg, i) => (
                <g
                  key={`seg-${i}`}
                  transform={`translate(${seg.cx},${seg.cy}) rotate(${angle})`}
                  style={legal ? { filter: "drop-shadow(0 0 3px #FDE68A) drop-shadow(0 0 2px #FDE68A)" } : undefined}
                >
                  {claimed ? (
                    <>
                      {/* Outer: full-size outline with neutral dark background */}
                      <rect
                        x={-seg.w / 2} y={-SEG_H / 2}
                        width={seg.w} height={SEG_H}
                        fill="#374151" fillOpacity={0.7}
                        stroke="#000" strokeWidth={1.5}
                        rx={2}
                      />
                      {/* Inner: inset player-color fill */}
                      <rect
                        x={-seg.w / 2 + CLAIM_INSET} y={-SEG_H / 2 + CLAIM_INSET}
                        width={Math.max(0, seg.w - CLAIM_INSET * 2)}
                        height={SEG_H - CLAIM_INSET * 2}
                        fill={fill}
                        rx={1}
                      />
                    </>
                  ) : (
                    <rect
                      x={-seg.w / 2} y={-SEG_H / 2}
                      width={seg.w} height={SEG_H}
                      fill={fill} fillOpacity={fillOpacity}
                      stroke="#000" strokeWidth={1.5}
                      rx={2}
                    />
                  )}
                  {/* Tunnel end-ticks */}
                  {route.tunnel && (
                    <>
                      <line x1={-seg.w / 2} y1={-tickExt} x2={-seg.w / 2} y2={tickExt}
                        stroke="#000" strokeWidth={2} />
                      <line x1={seg.w / 2} y1={-tickExt} x2={seg.w / 2} y2={tickExt}
                        stroke="#000" strokeWidth={2} />
                    </>
                  )}
                  {/* Ferry anchor on designated segment(s) */}
                  {ferrySegIndices.has(i) && (
                    <text
                      fontSize={8}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fill="#FDE68A"
                      stroke="#000"
                      strokeWidth={0.4}
                      style={{ pointerEvents: "none" }}
                    >
                      ⚓
                    </text>
                  )}
                </g>
              ))}

              {/* Wide transparent hit area for click detection */}
              <path
                d={hitPath}
                stroke="transparent"
                strokeWidth={16}
                fill="none"
                style={{ cursor: legal ? "pointer" : "default" }}
                onClick={() => handleRouteClick(route)}
              />
            </g>
          );
        })}

        {/* Cities */}
        {Object.entries(CITY_COORDS).map(([name, pos]) => {
          const cityIdx = cityNameToIdx.get(name);
          const canPlaceStation = cityIdx !== undefined && stationCityActions.has(cityIdx);
          return (
            <g
              key={name}
              style={{ cursor: canPlaceStation ? "pointer" : "default" }}
              onClick={() => handleCityClick(name)}
            >
              {/* Station-placement glow ring */}
              {canPlaceStation && (
                <circle cx={pos.x} cy={pos.y} r={10} fill="#60A5FA" fillOpacity={0.35}
                  stroke="#60A5FA" strokeWidth={1.5} strokeOpacity={0.7} />
              )}
              <circle cx={pos.x} cy={pos.y} r={6} fill={cityFill(name)} stroke="#374151" strokeWidth={1.5} />
              <text
                x={pos.x}
                y={pos.y - 9}
                fontSize={9}
                textAnchor="middle"
                fill="#111"
                stroke="#fff"
                strokeWidth={3}
                paintOrder="stroke"
                style={{ pointerEvents: "none", fontWeight: "600" }}
              >
                {name}
              </text>
            </g>
          );
        })}
      </svg>

      {pickerRouteIdx !== null && (
        <ColorPicker
          routeIdx={pickerRouteIdx}
          legalActions={legalActions}
          onPick={onAction}
          onClose={() => setPickerRouteIdx(null)}
        />
      )}

      {pickerStationCityIdx !== null && (
        <StationPicker
          cityName={cities[pickerStationCityIdx] ?? ""}
          actions={stationCityActions.get(pickerStationCityIdx) ?? []}
          onPick={onAction}
          onClose={() => setPickerStationCityIdx(null)}
        />
      )}
    </div>
  );
}
