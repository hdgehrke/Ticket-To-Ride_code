import { useMemo, useState } from "react";
import type { RouteInfo, PublicState, PrivateState } from "../types";
import { PLAYER_COLORS, COLOR_HEX, COLORS, ACTION_CLAIM_ROUTE_START } from "../types";
import { CITY_COORDS } from "../data/cities";

const SVG_W = 1000;
const SVG_H = 650;

// Number of routes (R) is needed to compute station action offsets
// We derive it dynamically from routes array length.

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
      options.push({
        colorIdx: ci,
        label: colorCode,
        hex: COLOR_HEX[colorCode],
        action,
      });
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

interface Props {
  publicState: PublicState;
  privateState: PrivateState;
  isMyTurn: boolean;
  onAction: (actionIdx: number) => void;
}

function getRouteCenter(city1: string, city2: string, parallelIndex: number): { x: number; y: number } {
  const c1 = CITY_COORDS[city1];
  const c2 = CITY_COORDS[city2];
  if (!c1 || !c2) return { x: 0, y: 0 };
  const mx = (c1.x + c2.x) / 2;
  const my = (c1.y + c2.y) / 2;
  if (parallelIndex === 0) return { x: mx, y: my };
  // offset perpendicular for parallel route
  const dx = c2.x - c1.x;
  const dy = c2.y - c1.y;
  const len = Math.sqrt(dx * dx + dy * dy) || 1;
  const perp = { x: -dy / len, y: dx / len };
  return { x: mx + perp.x * 8, y: my + perp.y * 8 };
}

function routeHitPath(city1: string, city2: string, parallelIndex: number): string {
  const c1 = CITY_COORDS[city1];
  const c2 = CITY_COORDS[city2];
  if (!c1 || !c2) return "";
  if (parallelIndex === 0) {
    return `M ${c1.x} ${c1.y} L ${c2.x} ${c2.y}`;
  }
  const dx = c2.x - c1.x;
  const dy = c2.y - c1.y;
  const len = Math.sqrt(dx * dx + dy * dy) || 1;
  const perp = { x: -dy / len * 8, y: dx / len * 8 };
  return `M ${c1.x + perp.x} ${c1.y + perp.y} L ${c2.x + perp.x} ${c2.y + perp.y}`;
}

export function MapSVG({ publicState, privateState, isMyTurn, onAction }: Props) {
  const [pickerRouteIdx, setPickerRouteIdx] = useState<number | null>(null);

  const claimedRoutes = publicState.claimed_routes;
  const legalActions = privateState.legal_actions;
  const routes = publicState.routes;

  // Which route indices are claimable by the current player
  const legalRouteSet = useMemo(() => {
    if (!isMyTurn) return new Set<number>();
    const s = new Set<number>();
    for (const a of legalActions) {
      if (a >= ACTION_CLAIM_ROUTE_START) {
        const offset = a - ACTION_CLAIM_ROUTE_START;
        const routeIdx = Math.floor(offset / 9);
        if (routeIdx < routes.length) s.add(routeIdx);
      }
    }
    return s;
  }, [legalActions, isMyTurn, routes.length]);

  function handleRouteClick(route: RouteInfo) {
    if (!isMyTurn || !legalRouteSet.has(route.index)) return;
    // Check how many color options exist
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

  function routeStroke(route: RouteInfo): string {
    const claimedBy = claimedRoutes[String(route.index)];
    if (claimedBy !== undefined) return PLAYER_COLORS[claimedBy];
    if (route.color === "X") return "#9CA3AF";
    return COLOR_HEX[route.color] ?? "#9CA3AF";
  }

  function routeOpacity(route: RouteInfo): number {
    const claimed = claimedRoutes[String(route.index)] !== undefined;
    if (claimed) return 1;
    if (isMyTurn && legalRouteSet.has(route.index)) return 0.9;
    return 0.45;
  }

  return (
    <div className="map-container">
      <svg
        viewBox={`0 0 ${SVG_W} ${SVG_H}`}
        className="map-svg"
        style={{ width: "100%", height: "100%" }}
      >
        {/* Background */}
        <rect width={SVG_W} height={SVG_H} fill="#1a3a2e" rx="8" />

        {/* Routes */}
        {routes.map(route => {
          const c1 = CITY_COORDS[route.city1];
          const c2 = CITY_COORDS[route.city2];
          if (!c1 || !c2) return null;

          const claimed = claimedRoutes[String(route.index)] !== undefined;
          const legal = isMyTurn && legalRouteSet.has(route.index);
          const stroke = routeStroke(route);
          const opacity = routeOpacity(route);
          const path = routeHitPath(route.city1, route.city2, route.parallel_index);

          return (
            <g key={route.index}>
              {/* Visible route line */}
              <path
                d={path}
                stroke={stroke}
                strokeWidth={claimed ? 6 : 5}
                strokeOpacity={opacity}
                strokeDasharray={route.tunnel ? "6 4" : undefined}
                fill="none"
                strokeLinecap="round"
              />
              {/* Glow for legal routes */}
              {legal && (
                <path
                  d={path}
                  stroke="#FDE68A"
                  strokeWidth={9}
                  strokeOpacity={0.3}
                  fill="none"
                  strokeLinecap="round"
                />
              )}
              {/* Ferry icon (locomotive required) */}
              {route.ferries > 0 && (() => {
                const center = getRouteCenter(route.city1, route.city2, route.parallel_index);
                return (
                  <text
                    x={center.x}
                    y={center.y + 4}
                    fontSize={10}
                    textAnchor="middle"
                    fill="#FDE68A"
                    style={{ pointerEvents: "none" }}
                  >
                    {route.ferries === 1 ? "⚓" : "⚓⚓"}
                  </text>
                );
              })()}
              {/* Clickable hit area */}
              <path
                d={path}
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
        {Object.entries(CITY_COORDS).map(([name, pos]) => (
          <g key={name}>
            <circle cx={pos.x} cy={pos.y} r={6} fill="#F9FAFB" stroke="#374151" strokeWidth={1.5} />
            <text
              x={pos.x}
              y={pos.y - 9}
              fontSize={9}
              textAnchor="middle"
              fill="#F9FAFB"
              style={{ pointerEvents: "none", fontWeight: "600", textShadow: "0 1px 2px #000" }}
            >
              {name}
            </text>
          </g>
        ))}
      </svg>

      {pickerRouteIdx !== null && (
        <ColorPicker
          routeIdx={pickerRouteIdx}
          legalActions={legalActions}
          onPick={onAction}
          onClose={() => setPickerRouteIdx(null)}
        />
      )}
    </div>
  );
}
