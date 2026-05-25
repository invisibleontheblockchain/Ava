"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { BlockData, BlockType } from "@/lib/types";

const COLORS: Record<BlockType, string> = {
  web: "#0ea5e9",
  prompt: "#8b5cf6",
  note: "#22c55e",
  table: "#f59e0b",
  list: "#ec4899",
  report: "#6366f1",
  memo: "#14b8a6",
  file: "#a855f7",
  youtube: "#ef4444",
  image: "#f97316",
  excel: "#10b981",
  presentation: "#3b82f6",
  dashboard: "#06b6d4",
  app: "#84cc16",
  code: "#64748b",
  connector: "#e11d48",
  human_gate: "#78716c",
};

const STATUS_DOT: Record<string, string> = {
  idle: "#94a3b8",
  running: "#fbbf24",
  complete: "#22c55e",
  error: "#ef4444",
};

export type BlockNodeProps = NodeProps & {
  data: BlockData & { blockType: BlockType };
};

function BaseBlockComponent({ data, selected, type }: BlockNodeProps) {
  const blockType = (type as BlockType) || data.blockType;
  const accent = COLORS[blockType] ?? "#64748b";
  const status = data.status ?? "idle";

  return (
    <div
      className={`block-node ${selected ? "block-node--selected" : ""}`}
      style={{ borderColor: accent }}
    >
      <Handle type="target" position={Position.Left} className="block-handle" />
      <header className="block-node__header" style={{ background: accent }}>
        <span
          className="block-node__status"
          style={{ background: STATUS_DOT[status] }}
          title={status}
        />
        <span className="block-node__type">{blockType}</span>
      </header>
      <div className="block-node__body">
        <strong>{data.title}</strong>
        {data.config?.url && (
          <p className="block-node__meta">{data.config.url}</p>
        )}
        {data.prompt && blockType !== "web" && (
          <p className="block-node__prompt">{data.prompt.slice(0, 120)}</p>
        )}
        {data.outputPreview && (
          <pre className="block-node__output">{data.outputPreview.slice(0, 400)}</pre>
        )}
      </div>
      <Handle type="source" position={Position.Right} className="block-handle" />
    </div>
  );
}

export const BaseBlock = memo(BaseBlockComponent);
