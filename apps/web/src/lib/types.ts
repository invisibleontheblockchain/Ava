import { z } from "zod";

export const blockTypeSchema = z.enum([
  "prompt",
  "web",
  "note",
  "table",
  "list",
  "report",
  "memo",
  "file",
  "youtube",
  "image",
  "excel",
  "presentation",
  "dashboard",
  "app",
  "code",
  "connector",
  "human_gate",
]);
export type BlockType = z.infer<typeof blockTypeSchema>;

export const blockStatusSchema = z.enum(["idle", "running", "complete", "error"]);
export type BlockStatus = z.infer<typeof blockStatusSchema>;

export const blockConfigSchema = z.object({
  model: z.string().optional(),
  temperature: z.number().optional(),
  max_tokens: z.number().optional(),
  system_prompt: z.string().optional(),
  url: z.string().optional(),
  export_pptx: z.boolean().optional(),
  connector_id: z.string().optional(),
  resource: z.string().optional(),
  approved: z.boolean().optional(),
});

export type BlockConfig = z.infer<typeof blockConfigSchema>;

export const blockDataSchema = z.object({
  title: z.string(),
  prompt: z.string().optional(),
  status: blockStatusSchema.default("idle"),
  config: blockConfigSchema.default({}),
  outputPreview: z.string().optional(),
  outputRef: z.string().optional(),
  fileArtifactId: z.string().optional(),
});

export type BlockData = z.infer<typeof blockDataSchema>;

export const canvasBlockSchema = z.object({
  id: z.string(),
  type: blockTypeSchema,
  position: z.object({ x: z.number(), y: z.number() }),
  data: blockDataSchema,
  connections: z.object({
    inputs: z.array(z.string()),
    outputs: z.array(z.string()),
  }),
});

export const canvasEdgeSchema = z.object({
  id: z.string(),
  source: z.string(),
  target: z.string(),
});

export const canvasGraphSchema = z.object({
  blocks: z.array(canvasBlockSchema),
  edges: z.array(canvasEdgeSchema),
});

export type CanvasGraph = z.infer<typeof canvasGraphSchema>;

export interface CanvasResponse {
  id: string;
  name: string;
  graph: CanvasGraph;
}

export interface RunResponse {
  id: string;
  canvas_id: string;
  status: string;
  thread_id: string;
}
