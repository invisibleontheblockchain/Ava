"use client";

import { useCallback, useMemo } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  addEdge,
  applyEdgeChanges,
  applyNodeChanges,
  type Connection,
  type Edge,
  type Node,
  type NodeChange,
  type EdgeChange,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { BaseBlock } from "@/components/blocks/BaseBlock";

const nodeTypes: NodeTypes = {
  web: BaseBlock,
  prompt: BaseBlock,
  note: BaseBlock,
  table: BaseBlock,
  list: BaseBlock,
  report: BaseBlock,
  memo: BaseBlock,
  file: BaseBlock,
  youtube: BaseBlock,
  image: BaseBlock,
  excel: BaseBlock,
  presentation: BaseBlock,
  dashboard: BaseBlock,
  app: BaseBlock,
  code: BaseBlock,
  connector: BaseBlock,
  human_gate: BaseBlock,
};

interface WorkflowCanvasProps {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: (nodes: Node[]) => void;
  onEdgesChange: (edges: Edge[]) => void;
  onSelectionChange?: (nodeId: string | null) => void;
  readOnly?: boolean;
}

export function WorkflowCanvas({
  nodes,
  edges,
  onNodesChange,
  onEdgesChange,
  onSelectionChange,
  readOnly = false,
}: WorkflowCanvasProps) {
  const handleNodesChange = useCallback(
    (changes: NodeChange[]) => {
      onNodesChange(applyNodeChanges(changes, nodes));
    },
    [nodes, onNodesChange]
  );

  const handleEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      onEdgesChange(applyEdgeChanges(changes, edges));
    },
    [edges, onEdgesChange]
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      onEdgesChange(addEdge(connection, edges));
    },
    [edges, onEdgesChange]
  );

  const defaultEdgeOptions = useMemo(() => ({ animated: true }), []);

  return (
    <div className="canvas-shell">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        fitView
        minZoom={0.2}
        maxZoom={1.5}
        nodesDraggable={!readOnly}
        nodesConnectable={!readOnly}
        elementsSelectable={!readOnly}
        onSelectionChange={({ nodes: sel }) =>
          onSelectionChange?.(sel[0]?.id ?? null)
        }
      >
        <Background gap={16} size={1} />
        <Controls />
        <MiniMap zoomable pannable />
      </ReactFlow>
    </div>
  );
}
