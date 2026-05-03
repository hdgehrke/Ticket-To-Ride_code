import { useState } from "react";
import type { Ticket } from "../types";
import { ACTION_KEEP_TICKETS_START, ACTION_KEEP_INIT_TICKETS_START } from "../types";

interface Props {
  tickets: Ticket[];
  pendingTickets?: Ticket[];
  legalActions: number[];
  isMyTurn: boolean;
  phase: string;
  onKeepTickets: (actionIdx: number) => void;
  onDrawTickets: () => void;
  onTicketHover: (ticket: Ticket | null) => void;
}

export function TicketPanel({
  tickets, pendingTickets, legalActions, isMyTurn, phase, onKeepTickets, onDrawTickets, onTicketHover,
}: Props) {
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const isTicketSelection = phase === "TICKET_SELECTION";
  const isInitSelection = phase === "INITIAL_TICKET_SELECTION" || phase === "MEGA_LONG_SELECTION";
  const showing = pendingTickets && pendingTickets.length > 0;

  function toggleSelect(i: number) {
    setSelected(s => {
      const next = new Set(s);
      if (next.has(i)) next.delete(i);
      else next.add(i);
      return next;
    });
  }

  function computeActionIdx(): number | null {
    if (!showing) return null;
    if (isInitSelection) {
      // bitmask over up to 5 tickets, action = 28 + mask
      let mask = 0;
      selected.forEach(i => { mask |= (1 << i); });
      const action = ACTION_KEEP_INIT_TICKETS_START + mask;
      return legalActions.includes(action) ? action : null;
    } else {
      // TICKET_SELECTION: bitmask 1–15 over up to 4 tickets, action = 13 + mask - 1
      let mask = 0;
      selected.forEach(i => { mask |= (1 << i); });
      if (mask === 0) return null;
      const action = ACTION_KEEP_TICKETS_START + mask - 1;
      return legalActions.includes(action) ? action : null;
    }
  }

  function confirm() {
    const action = computeActionIdx();
    if (action !== null) {
      onKeepTickets(action);
      setSelected(new Set());
    }
  }

  const actionIdx = computeActionIdx();
  const canDrawTickets = isMyTurn && legalActions.includes(6);

  return (
    <div className="ticket-panel">
      <h3>Tickets</h3>

      {/* Ticket selection modal */}
      {showing && (isTicketSelection || isInitSelection) && (
        <div className="ticket-selection">
          <p><strong>Choose tickets to keep{isTicketSelection ? " (≥1)" : ""}:</strong></p>
          {pendingTickets!.map((t, i) => (
            <label
              key={i}
              className={`ticket-option ${selected.has(i) ? "selected" : ""}`}
              onMouseEnter={() => onTicketHover(t)}
              onMouseLeave={() => onTicketHover(null)}
            >
              <input
                type="checkbox"
                checked={selected.has(i)}
                onChange={() => toggleSelect(i)}
              />
              {t.city1} → {t.city2} ({t.points}pts{t.is_long ? ", long" : ""})
            </label>
          ))}
          <button
            onClick={confirm}
            disabled={actionIdx === null}
            className="btn-primary"
          >
            Confirm
          </button>
        </div>
      )}

      {/* Current tickets — incomplete first, then complete */}
      <div className="ticket-list">
        {tickets.length === 0 && <p className="muted">No tickets yet.</p>}
        {[...tickets]
          .sort((a, b) => {
            const aComplete = a.completed ?? false;
            const bComplete = b.completed ?? false;
            return Number(aComplete) - Number(bComplete);
          })
          .map((t, i) => (
            <div
              key={i}
              className={`ticket-item ${t.completed ? "ticket-item--done" : "ticket-item--todo"}`}
              onMouseEnter={() => onTicketHover(t)}
              onMouseLeave={() => onTicketHover(null)}
            >
              <span className="ticket-status">{t.completed ? "✓" : "○"}</span>
              <span className="ticket-route">{t.city1} → {t.city2}</span>
              <span className="ticket-pts">{t.points}pts</span>
              {t.is_long && <span className="long-badge">L</span>}
            </div>
          ))}
      </div>

      {canDrawTickets && (
        <button onClick={onDrawTickets} className="btn-secondary draw-tickets-btn">
          Draw Tickets
        </button>
      )}
    </div>
  );
}
