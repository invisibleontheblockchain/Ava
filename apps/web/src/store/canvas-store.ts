import type { Edge, Node } from "@xyflow/react";
import { create } from "zustand";
import { useShallow } from "zustand/react/shallow";

import type { BlockStatus } from "@/lib/types";

interface CanvasStore {
  canvasId: string | null;
  runId: string | null;
  runStatus: string | null;
  log: string[];
  nodes: Node[];
  edges: Edge[];
  selectedNodeId: string | null;
  running: boolean;

  setCanvasId: (id: string | null) => void;
  setRun: (runId: string | null, status: string | null) => void;
  setRunning: (running: boolean) => void;
  setGraph: (nodes: Node[], edges: Edge[]) => void;
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  setSelectedNodeId: (id: string | null) => void;
  appendLog: (line: string) => void;
  clearLog: () => void;
  updateNodeData: (nodeId: string, patch: Record<string, unknown>) => void;
  updateNodeStatus: (
    nodeId: string,
    status: BlockStatus,
    patch?: { outputPreview?: string; outputRef?: string; fileArtifactId?: string }
  ) => void;
  appendNodeToken: (nodeId: string, token: string) => void;
  resetNodeOutputs: () => void;
}

export const useCanvasStore = create<CanvasStore>((set, get) => ({
  canvasId: null,
  runId: null,
  runStatus: null,
  log: [],
  nodes: [],
  edges: [],
  selectedNodeId: null,
  running: false,

  setCanvasId: (id) => set({ canvasId: id }),
  setRun: (runId, runStatus) => set({ runId, runStatus }),
  setRunning: (running) => set({ running }),
  setGraph: (nodes, edges) => set({ nodes, edges }),
  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),
  setSelectedNodeId: (id) => set({ selectedNodeId: id }),
  appendLog: (line) => set({ log: [...get().log.slice(-200), line] }),
  clearLog: () => set({ log: [] }),

  updateNodeData: (nodeId, patch) =>
    set({
      nodes: get().nodes.map((n) =>
        n.id === nodeId ? { ...n, data: { ...n.data, ...patch } } : n
      ),
    }),

  updateNodeStatus: (nodeId, status, patch) =>
    set({
      nodes: get().nodes.map((n) =>
        n.id === nodeId
          ? {
              ...n,
              data: {
                ...n.data,
                status,
                ...(patch?.outputPreview !== undefined
                  ? { outputPreview: patch.outputPreview }
                  : {}),
                ...(patch?.outputRef !== undefined ? { outputRef: patch.outputRef } : {}),
                ...(patch?.fileArtifactId !== undefined
                  ? { fileArtifactId: patch.fileArtifactId }
                  : {}),
              },
            }
          : n
      ),
    }),

  appendNodeToken: (nodeId, token) =>
    set({
      nodes: get().nodes.map((n) =>
        n.id === nodeId
          ? {
              ...n,
              data: {
                ...n.data,
                status: "running" as BlockStatus,
                outputPreview: ((n.data.outputPreview as string) || "") + token,
              },
            }
          : n
      ),
    }),

  resetNodeOutputs: () =>
    set({
      nodes: get().nodes.map((n) => ({
        ...n,
        data: {
          ...n.data,
          status: "idle" as BlockStatus,
          outputPreview: undefined,
          outputRef: undefined,
          fileArtifactId: undefined,
        },
      })),
    }),
}));

/** Shallow selectors — Document 2 §3 performance requirement */
export function useCanvasNodes() {
  return useCanvasStore(useShallow((s) => s.nodes));
}

export function useCanvasEdges() {
  return useCanvasStore(useShallow((s) => s.edges));
}
