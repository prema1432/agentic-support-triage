export interface Ticket {
  id: string;
  subject: string;
  body: string;
  customer_tier: string;
  status: "pending_review" | "approved" | "rejected" | "resolved";
  priority: string | null;
  category: string | null;
  draft_reply: string | null;
  created_at: string | null;
}

const BASE = "/api";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`API ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export async function listTickets(): Promise<Ticket[]> {
  return json(await fetch(`${BASE}/tickets`));
}

export async function createTicket(payload: { subject: string; body: string }): Promise<Ticket> {
  return json(
    await fetch(`${BASE}/tickets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}

export async function runAgents(ticketId: string): Promise<{ needs_human: boolean; status: string }> {
  return json(await fetch(`${BASE}/tickets/${ticketId}/run`, { method: "POST" }));
}

export async function approveTicket(
  ticketId: string,
  payload: { decision: "approved" | "rejected"; reviewer: string; note?: string }
): Promise<Ticket> {
  return json(
    await fetch(`${BASE}/tickets/${ticketId}/approval`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  );
}
