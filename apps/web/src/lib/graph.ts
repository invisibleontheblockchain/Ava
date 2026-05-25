import type { Edge, Node } from "@xyflow/react";
import type { BlockData, BlockType, CanvasGraph } from "./types";

export const PHASE1_BLOCK_TYPES: { type: BlockType; label: string }[] = [
  { type: "web", label: "Web" },
  { type: "prompt", label: "Prompt" },
  { type: "note", label: "Note" },
  { type: "table", label: "Table" },
  { type: "list", label: "List" },
];

export const PHASE2_BLOCK_TYPES: { type: BlockType; label: string }[] = [
  { type: "report", label: "Report" },
  { type: "memo", label: "Memo" },
  { type: "file", label: "File" },
  { type: "youtube", label: "YouTube" },
  { type: "image", label: "Image" },
];

export const PHASE5_BLOCK_TYPES: { type: BlockType; label: string }[] = [
  { type: "excel", label: "Excel" },
  { type: "presentation", label: "Slides" },
  { type: "dashboard", label: "Dashboard" },
  { type: "app", label: "App" },
  { type: "code", label: "Code" },
  { type: "connector", label: "Connector" },
  { type: "human_gate", label: "Human gate" },
];

export function defaultBlockData(type: BlockType, title: string): BlockData {
  const base: BlockData = {
    title,
    status: "idle",
    config: {},
    prompt: "",
  };
  if (type === "web") {
    base.config = { url: "https://example.com" };
    base.prompt = "https://example.com";
  }
  if (type === "prompt") {
    base.prompt = "Summarize the upstream web content in 3 bullet points.";
  }
  if (type === "note") {
    base.prompt = "Final synthesized notes";
    base.config = { export_pptx: false };
  }
  if (type === "report") base.prompt = "Write a structured report from upstream context.";
  if (type === "memo") base.prompt = "Write an internal memo.";
  if (type === "file") base.prompt = "/path/to/file.txt";
  if (type === "youtube") {
    base.config = { url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ" };
    base.prompt = base.config.url;
  }
  if (type === "image") base.prompt = "Describe the visual to generate.";
  if (type === "excel") base.prompt = "Build spreadsheet from upstream data.";
  if (type === "presentation") {
    base.prompt = "Outline slide deck from context.";
    base.config = { export_pptx: true };
  }
  if (type === "dashboard") base.prompt = "Metrics dashboard from upstream.";
  if (type === "app") base.prompt = "Simple HTML UI from context.";
  if (type === "code") base.prompt = "print('hello from Ava')";
  if (type === "connector") {
    base.config = { connector_id: "google_drive", resource: "sample-doc" };
    base.prompt = "sample-doc";
  }
  if (type === "human_gate") {
    base.config = { approved: false };
    base.prompt = "Approve to continue pipeline.";
  }
  return base;
}

export function createDemoGraph(): CanvasGraph {
  return {
    blocks: [
      {
        id: "web-1",
        type: "web",
        position: { x: 80, y: 120 },
        data: defaultBlockData("web", "Fetch source"),
        connections: { inputs: [], outputs: ["prompt-1"] },
      },
      {
        id: "prompt-1",
        type: "prompt",
        position: { x: 380, y: 120 },
        data: defaultBlockData("prompt", "Analyze"),
        connections: { inputs: ["web-1"], outputs: ["note-1"] },
      },
      {
        id: "note-1",
        type: "note",
        position: { x: 680, y: 120 },
        data: defaultBlockData("note", "Output"),
        connections: { inputs: ["prompt-1"], outputs: [] },
      },
    ],
    edges: [
      { id: "e-web-prompt", source: "web-1", target: "prompt-1" },
      { id: "e-prompt-note", source: "prompt-1", target: "note-1" },
    ],
  };
}

export function graphToFlow(graph: CanvasGraph): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = graph.blocks.map((b) => ({
    id: b.id,
    type: b.type,
    position: b.position,
    data: { ...b.data, blockType: b.type },
  }));
  const edges: Edge[] = graph.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    animated: true,
  }));
  return { nodes, edges };
}

export function flowToGraph(nodes: Node[], edges: Edge[]): CanvasGraph {
  const blocks = nodes.map((n) => {
    const inputs = edges.filter((e) => e.target === n.id).map((e) => e.source);
    const outputs = edges.filter((e) => e.source === n.id).map((e) => e.target);
    const { blockType, ...data } = n.data as BlockData & { blockType?: BlockType };
    return {
      id: n.id,
      type: (n.type as BlockType) || "prompt",
      position: n.position,
      data: {
        title: data.title ?? n.id,
        prompt: data.prompt,
        status: data.status ?? "idle",
        config: data.config ?? {},
        outputPreview: data.outputPreview,
      },
      connections: { inputs, outputs },
    };
  });
  return {
    blocks,
    edges: edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
    })),
  };
}

export function newBlockId(type: BlockType): string {
  return `${type}-${crypto.randomUUID().slice(0, 8)}`;
}
