"use client";

import { useState } from "react";
import { confirmPlan, startPlanning } from "@/lib/api";

export function PlanningPanel() {
  const [brief, setBrief] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [planJson, setPlanJson] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [runId, setRunId] = useState<string | null>(null);

  const onPlan = async () => {
    const res = await startPlanning(brief);
    setSessionId(res.session_id);
    setStatus(res.status);
    setPlanJson(JSON.stringify(res.plan, null, 2));
  };

  const onConfirm = async () => {
    if (!sessionId) return;
    const plan = planJson ? JSON.parse(planJson) : undefined;
    const res = await confirmPlan(sessionId, plan);
    setRunId(res.run_id);
    setStatus("queued");
  };

  return (
    <aside className="planning-panel">
      <h3>L1 Planner</h3>
      <textarea
        value={brief}
        onChange={(e) => setBrief(e.target.value)}
        placeholder="Describe your goal in natural language…"
        rows={4}
      />
      <button type="button" onClick={onPlan} disabled={!brief.trim()}>
        Generate plan
      </button>
      {planJson && (
        <textarea
          className="planning-panel__plan"
          value={planJson}
          onChange={(e) => setPlanJson(e.target.value)}
          rows={10}
        />
      )}
      {sessionId && (
        <button type="button" onClick={onConfirm}>
          Confirm & run swarm
        </button>
      )}
      {status && <p className="planning-panel__status">Status: {status}</p>}
      {runId && <p className="planning-panel__status">Run: {runId}</p>}
    </aside>
  );
}
