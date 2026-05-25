"use client";

import { useEffect, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type Connector = {
  id: string;
  name: string;
  namespace: string;
  installed?: boolean;
  verified?: boolean;
};

export function MarketplacePanel() {
  const [items, setItems] = useState<Connector[]>([]);

  useEffect(() => {
    fetch(`${API}/marketplace/connectors`)
      .then((r) => r.json())
      .then((d) => setItems(d.connectors ?? []))
      .catch(() => setItems([]));
  }, []);

  const connect = async (id: string) => {
    await fetch(`${API}/connectors/oauth/connect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: "default", connector_id: id }),
    });
    const res = await fetch(`${API}/marketplace/connectors`);
    const d = await res.json();
    setItems(d.connectors ?? []);
  };

  return (
    <aside className="marketplace-panel">
      <h3>Connectors</h3>
      <ul>
        {items.map((c) => (
          <li key={c.id}>
            <strong>{c.name}</strong>
            <span className="marketplace-panel__ns">{c.namespace}</span>
            {c.installed ? (
              <span className="marketplace-panel__badge">installed</span>
            ) : (
              <button type="button" onClick={() => connect(c.id)}>
                Connect
              </button>
            )}
          </li>
        ))}
      </ul>
    </aside>
  );
}
