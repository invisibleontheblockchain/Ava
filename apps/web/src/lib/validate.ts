import { canvasGraphSchema, type CanvasGraph } from "./types";

export function validateCanvasGraph(graph: unknown): CanvasGraph {
  return canvasGraphSchema.parse(graph);
}
