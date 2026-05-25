"use client";

import type { Node, Edge } from "@xyflow/react";
import {
  PHASE1_BLOCK_TYPES,
  PHASE2_BLOCK_TYPES,
  PHASE5_BLOCK_TYPES,
  defaultBlockData,
  newBlockId,
} from "@/lib/graph";
import type { BlockType } from "@/lib/types";

interface CanvasToolbarProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: (nodes: Node[]) => void;
  onRun: () => void;
  onSwarm: () => void;
  onResume: () => void;
  onSave: () => void;
  running: boolean;
  runId: string | null;
}

export function CanvasToolbar({
  nodes,
  edges,
  onNodesChange,
  onRun,
  onSwarm,
  onResume,
  onSave,
  running,
  runId,
}: CanvasToolbarProps) {
  const addBlock = (type: BlockType) => {
    const id = newBlockId(type);
    const y = 80 + nodes.length * 40;
    const node: Node = {
      id,
      type,
      position: { x: 100 + nodes.length * 30, y },
      data: { ...defaultBlockData(type, `${type} block`), blockType: type },
    };
    onNodesChange([...nodes, node]);
  };

  return (
    <div className="toolbar">
      <div className="toolbar__brand">
        <strong>Ava</strong>
        <span className="toolbar__phase">Phase 5</span>
      </div>
      <div className="toolbar__blocks">
        {[...PHASE1_BLOCK_TYPES, ...PHASE2_BLOCK_TYPES, ...PHASE5_BLOCK_TYPES].map(({ type, label }) => (
          <button
            key={type}
            type="button"
            className="toolbar__btn toolbar__btn--ghost"
            onClick={() => addBlock(type)}
            disabled={running}
          >
            + {label}
          </button>
        ))}
      </div>
      <div className="toolbar__actions">
        <button type="button" className="toolbar__btn" onClick={onSave} disabled={running}>
          Save
        </button>
        <button
          type="button"
          className="toolbar__btn toolbar__btn--primary"
          onClick={onRun}
          disabled={running}
        >
          {running ? "Running…" : "Run canvas"}
        </button>
        <button
          type="button"
          className="toolbar__btn"
          onClick={onSwarm}
          disabled={running}
          title="L2/L2.5 demo plan — 3 personas in parallel"
        >
          Run swarm
        </button>
        {runId && (
          <button
            type="button"
            className="toolbar__btn"
            onClick={onResume}
            disabled={running}
            title="Resume from LangGraph checkpoint"
          >
            Resume
          </button>
        )}
      </div>
    </div>
  );
}
