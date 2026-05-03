// Types matching the FastAPI server protocol (session.py)

export interface RouteInfo {
  index: number;
  city1: string;
  city2: string;
  length: number;
  color: string; // "P"|"W"|"B"|"Y"|"O"|"K"|"R"|"G"|"X"
  ferries: number;
  tunnel: boolean;
  parallel_index: number;
}

export interface PlayerPublicInfo {
  id: number;
  name: string;
  is_ai: boolean;
  trains: number;
  stations: number;
  score: number;
  hand_total: number;
  ticket_count: number;
  station_cities: string[];
}

export interface PublicState {
  session_id: string;
  phase: string;
  current_player: number;
  players: PlayerPublicInfo[];
  face_up: (string | null)[];
  deck_size: number;
  discard_size: number;
  claimed_routes: Record<string, number>; // route_idx → player_id
  cities: string[];   // ordered city names — index matches PLACE_STATION action city_idx
  routes: RouteInfo[];
  tunnel_cards: string[] | null;
  tunnel_extra_cost: number | null;
  tunnel_pay_action: number | null;
  tunnel_decline_action: number | null;
}

export interface Ticket {
  city1: string;
  city2: string;
  points: number;
  is_long: boolean;
  completed?: boolean; // present in hand tickets; absent in pending tickets
}

export interface PrivateState {
  hand: Record<string, number>; // color → count
  tickets: Ticket[];
  pending_tickets?: Ticket[];
  legal_actions: number[];
}

export interface TicketResult {
  city1: string;
  city2: string;
  points: number;
  completed: boolean;
}

export interface PlayerScoreBreakdown {
  route_score: number;
  unused_stations: number;
  station_bonus: number;
  tickets: TicketResult[];
  ticket_total: number;
  longest_route_length: number;
  longest_route_bonus: number;
  total: number;
}

export type ServerMessage =
  | { type: "state"; public: PublicState; private: PrivateState }
  | { type: "error"; message: string }
  | { type: "game_over"; scores: number[]; players: string[]; breakdown: PlayerScoreBreakdown[] };

// Action space layout from actions.py
export const ACTION_DRAW_FACE_UP_START = 0;      // 0–4
export const ACTION_DRAW_DECK = 5;
export const ACTION_DRAW_TICKETS = 6;
export const ACTION_DRAW_FACE_UP_SECOND_START = 7; // 7–11
export const ACTION_DRAW_DECK_SECOND = 12;
export const ACTION_KEEP_TICKETS_START = 13;     // 13–27 (bitmask 1–15)
export const ACTION_KEEP_INIT_TICKETS_START = 28; // 28–59 (bitmask 0–31)
export const ACTION_CLAIM_ROUTE_START = 60;      // 60 + route_idx*9 + color_idx

// Color index mapping (matches COLORS list in info.py)
export const COLORS = ["P", "W", "B", "Y", "O", "K", "R", "G"] as const;
export const LOCO = "L";
export const GRAY = "X";

export const COLOR_NAMES: Record<string, string> = {
  P: "Purple", W: "White", B: "Blue", Y: "Yellow",
  O: "Orange", K: "Black", R: "Red", G: "Green",
  L: "Locomotive", X: "Gray",
};

export const COLOR_HEX: Record<string, string> = {
  P: "#8B5CF6", W: "#F8FAFC", B: "#3B82F6", Y: "#EAB308",
  O: "#F97316", K: "#1F2937", R: "#EF4444", G: "#22C55E",
  L: "#6B7280", X: "#9CA3AF",
};

// Player colors for rendering claimed routes
export const PLAYER_COLORS = ["#DC2626", "#2563EB", "#16A34A", "#D97706", "#7C3AED"];
export const PLAYER_NAMES_COLOR = ["Red", "Blue", "Green", "Yellow", "Purple"];
