import { useCallback, useEffect, useState } from "react";
import { approveTicket, createTicket, listTickets, runAgents, Ticket } from "./api";

const STATUS_STYLES: Record<string, string> = {
  pending_review: "bg-amber-100 text-amber-800",
  approved: "bg-emerald-100 text-emerald-800",
  rejected: "bg-rose-100 text-rose-800",
  resolved: "bg-sky-100 text-sky-800",
};

export default function App() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setTickets(await listTickets());
    } catch (e) {
      setError(String(e));
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const submit = async () => {
    if (subject.length < 3 || body.length < 10) return;
    setBusy("create");
    try {
      await createTicket({ subject, body });
      setSubject("");
      setBody("");
      await refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(null);
    }
  };

  const run = async (id: string) => {
    setBusy(id);
    try {
      await runAgents(id);
      await refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(null);
    }
  };

  const decide = async (id: string, decision: "approved" | "rejected") => {
    setBusy(id);
    try {
      await approveTicket(id, { decision, reviewer: "web-reviewer" });
      await refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">Agentic Support Triage</h1>
            <p className="text-sm text-slate-500">
              Multi-agent workflow · tool calling · human-in-the-loop review
            </p>
          </div>
          <span className="text-xs font-mono bg-slate-100 px-2 py-1 rounded">FastAPI + MongoDB + React</span>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8 space-y-8">
        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-700 rounded-lg px-4 py-3 text-sm">
            {error}
          </div>
        )}

        <section className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="font-medium mb-4">New ticket</h2>
          <div className="space-y-3">
            <input
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
              placeholder="Subject (e.g. Payment failing on checkout)"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
            />
            <textarea
              className="w-full border border-slate-300 rounded-lg px-3 py-2 text-sm"
              rows={3}
              placeholder="Describe the issue…"
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
            <button
              className="bg-slate-900 text-white rounded-lg px-4 py-2 text-sm font-medium disabled:opacity-50"
              onClick={submit}
              disabled={busy === "create"}
            >
              {busy === "create" ? "Creating…" : "Create ticket"}
            </button>
          </div>
        </section>

        <section className="space-y-4">
          <h2 className="font-medium">Queue ({tickets.length})</h2>
          {tickets.length === 0 && (
            <p className="text-sm text-slate-500">No tickets yet — create one above.</p>
          )}
          {tickets.map((t) => (
            <article key={t.id} className="bg-white rounded-xl border border-slate-200 p-5 space-y-3">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 className="font-medium">{t.subject}</h3>
                  <p className="text-sm text-slate-600">{t.body}</p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${STATUS_STYLES[t.status] ?? "bg-slate-100"}`}>
                  {t.status}
                </span>
              </div>

              {(t.priority || t.category) && (
                <div className="flex gap-2 text-xs">
                  {t.priority && <span className="bg-slate-100 px-2 py-0.5 rounded">priority: {t.priority}</span>}
                  {t.category && <span className="bg-slate-100 px-2 py-0.5 rounded">category: {t.category}</span>}
                </div>
              )}

              {t.draft_reply && (
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm">
                  <span className="text-xs font-medium text-slate-500 block mb-1">Agent draft reply</span>
                  {t.draft_reply}
                </div>
              )}

              <div className="flex gap-2">
                <button
                  className="border border-slate-300 rounded-lg px-3 py-1.5 text-sm disabled:opacity-50"
                  onClick={() => run(t.id)}
                  disabled={busy === t.id}
                >
                  {busy === t.id ? "Running agents…" : "Run agents"}
                </button>
                {t.status === "pending_review" && t.priority && (
                  <>
                    <button
                      className="bg-emerald-600 text-white rounded-lg px-3 py-1.5 text-sm disabled:opacity-50"
                      onClick={() => decide(t.id, "approved")}
                      disabled={busy === t.id}
                    >
                      Approve
                    </button>
                    <button
                      className="bg-rose-600 text-white rounded-lg px-3 py-1.5 text-sm disabled:opacity-50"
                      onClick={() => decide(t.id, "rejected")}
                      disabled={busy === t.id}
                    >
                      Reject
                    </button>
                  </>
                )}
              </div>
            </article>
          ))}
        </section>
      </main>
    </div>
  );
}
