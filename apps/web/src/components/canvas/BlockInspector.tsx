"use client";

import { useEffect, useState } from "react";
import { useCanvasStore } from "@/store/canvas-store";
import type { BlockData, BlockType } from "@/lib/types";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function BlockInspector() {
  const selectedNodeId = useCanvasStore((s) => s.selectedNodeId);
  const nodes = useCanvasStore((s) => s.nodes);
  const runId = useCanvasStore((s) => s.runId);
  const updateNodeData = useCanvasStore((s) => s.updateNodeData);
  const running = useCanvasStore((s) => s.running);
  const [connectors, setConnectors] = useState<{ id: string; name: string }[]>([]);

  useEffect(() => {
    fetch(`${API}/connectors`)
      .then((r) => r.json())
      .then((d) => setConnectors(Array.isArray(d) ? d : []))
      .catch(() => setConnectors([]));
  }, []);

  const node = nodes.find((n) => n.id === selectedNodeId);
  if (!node) {
    return (
      <aside className="inspector">
        <h3>Block inspector</h3>
        <p className="inspector__hint">Select a block to edit fields and model routing.</p>
      </aside>
    );
  }

  const blockType = node.type as BlockType;
  const data = node.data as BlockData;
  const config = (data.config ?? {}) as Record<string, unknown>;

  const oauthConnect = async () => {
    const cid = String(config.connector_id ?? "google_drive");
    await fetch(`${API}/connectors/oauth/connect`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: "default", connector_id: cid }),
    });
  };

  const approveGate = async () => {
    if (!runId) return;
    await fetch(`${API}/runs/${runId}/approve?block_id=${node.id}`, { method: "POST" });
    updateNodeData(node.id, { config: { ...config, approved: true } });
  };

  return (
    <aside className="inspector">
      <h3>{String(data.title)}</h3>
      <p className="inspector__type">{blockType}</p>

      <label className="inspector__label">
        Title
        <input
          className="inspector__input"
          value={String(data.title ?? "")}
          disabled={running}
          onChange={(e) => updateNodeData(node.id, { title: e.target.value })}
        />
      </label>

      {(blockType === "prompt" || blockType === "report" || blockType === "memo") && (
        <label className="inspector__label">
          Model override
          <input
            className="inspector__input"
            placeholder="gpt-4o"
            value={String(config.model ?? "")}
            disabled={running}
            onChange={(e) =>
              updateNodeData(node.id, { config: { ...config, model: e.target.value } })
            }
          />
        </label>
      )}

      {blockType === "web" && (
        <label className="inspector__label">
          URL
          <input
            className="inspector__input"
            value={String(config.url ?? data.prompt ?? "")}
            disabled={running}
            onChange={(e) =>
              updateNodeData(node.id, {
                prompt: e.target.value,
                config: { ...config, url: e.target.value },
              })
            }
          />
        </label>
      )}

      {["prompt", "note", "report", "memo", "presentation", "app", "code", "image"].includes(
        blockType
      ) && (
        <label className="inspector__label">
          Prompt / instructions
          <textarea
            className="inspector__textarea"
            rows={5}
            value={String(data.prompt ?? "")}
            disabled={running}
            onChange={(e) => updateNodeData(node.id, { prompt: e.target.value })}
          />
        </label>
      )}

      {blockType === "connector" && (
        <>
          <label className="inspector__label">
            Connector
            <select
              className="inspector__input"
              value={String(config.connector_id ?? "google_drive")}
              disabled={running}
              onChange={(e) =>
                updateNodeData(node.id, {
                  config: { ...config, connector_id: e.target.value },
                })
              }
            >
              {connectors.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <label className="inspector__label">
            Resource
            <input
              className="inspector__input"
              value={String(config.resource ?? data.prompt ?? "")}
              disabled={running}
              onChange={(e) =>
                updateNodeData(node.id, {
                  prompt: e.target.value,
                  config: { ...config, resource: e.target.value },
                })
              }
            />
          </label>
          <button type="button" className="inspector__btn" onClick={oauthConnect}>
            OAuth connect
          </button>
        </>
      )}

      {blockType === "human_gate" && (
        <>
          <label className="inspector__check">
            <input
              type="checkbox"
              checked={Boolean(config.approved)}
              disabled={running}
              onChange={(e) =>
                updateNodeData(node.id, {
                  config: { ...config, approved: e.target.checked },
                })
              }
            />
            Approved (manual)
          </label>
          {runId && (
            <button type="button" className="inspector__btn" onClick={approveGate}>
              Approve & resume run
            </button>
          )}
        </>
      )}

      {blockType === "note" && (
        <label className="inspector__check">
          <input
            type="checkbox"
            checked={Boolean(config.export_pptx)}
            disabled={running}
            onChange={(e) =>
              updateNodeData(node.id, {
                config: { ...config, export_pptx: e.target.checked },
              })
            }
          />
          Export .pptx on complete
        </label>
      )}

      {data.outputRef && (
        <p className="inspector__meta">output_ref: {String(data.outputRef)}</p>
      )}
      {data.fileArtifactId && (
        <p className="inspector__meta">
          artifact:{" "}
          <a href={`${API}/runs/${runId}/artifacts/${data.fileArtifactId}`}>download</a>
        </p>
      )}
    </aside>
  );
}
