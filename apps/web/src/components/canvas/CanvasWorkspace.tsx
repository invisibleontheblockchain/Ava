"use client";

import { useCallback, useEffect } from "react";
import {
  artifactDownloadUrl,
  createCanvas,
  getBlockOutput,
  runEventsUrl,
  resumeRun,
  startRun,
  startSwarmRun,
  updateCanvas,
} from "@/lib/api";
import {
  createDemoGraph,
  flowToGraph,
  graphToFlow,
} from "@/lib/graph";
import { validateCanvasGraph } from "@/lib/validate";
import { useCanvasStore } from "@/store/canvas-store";
import { BlockInspector } from "./BlockInspector";
import { CanvasToolbar } from "./CanvasToolbar";
import { useCollabSync } from "@/hooks/useCollabSync";
import { MarketplacePanel } from "@/components/marketplace/MarketplacePanel";
import { PlanningPanel } from "@/components/planning/PlanningPanel";
import { WorkflowCanvas } from "./WorkflowCanvas";

export function CanvasWorkspace() {
  const canvasId = useCanvasStore((s) => s.canvasId);
  const runId = useCanvasStore((s) => s.runId);
  const runStatus = useCanvasStore((s) => s.runStatus);
  const log = useCanvasStore((s) => s.log);
  const nodes = useCanvasStore((s) => s.nodes);
  const edges = useCanvasStore((s) => s.edges);
  const running = useCanvasStore((s) => s.running);

  const setCanvasId = useCanvasStore((s) => s.setCanvasId);
  const setRun = useCanvasStore((s) => s.setRun);
  const setRunning = useCanvasStore((s) => s.setRunning);
  const setGraph = useCanvasStore((s) => s.setGraph);
  const setNodes = useCanvasStore((s) => s.setNodes);
  const setEdges = useCanvasStore((s) => s.setEdges);
  const setSelectedNodeId = useCanvasStore((s) => s.setSelectedNodeId);
  const appendLog = useCanvasStore((s) => s.appendLog);
  const clearLog = useCanvasStore((s) => s.clearLog);
  const updateNodeStatus = useCanvasStore((s) => s.updateNodeStatus);
  const appendNodeToken = useCanvasStore((s) => s.appendNodeToken);
  const resetNodeOutputs = useCanvasStore((s) => s.resetNodeOutputs);

  useCollabSync(canvasId, nodes, edges, setNodes, setEdges);

  useEffect(() => {
    const demo = graphToFlow(createDemoGraph());
    setGraph(demo.nodes, demo.edges);
  }, [setGraph]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const canvas = await createCanvas("Phase 1 demo");
        if (!cancelled) {
          setCanvasId(canvas.id);
          appendLog(`Canvas ${canvas.id} ready`);
        }
      } catch (e) {
        appendLog(`API: ${e instanceof Error ? e.message : String(e)}`);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [appendLog, setCanvasId]);

  const saveCanvas = useCallback(async () => {
    if (!canvasId) return;
    const graph = validateCanvasGraph(flowToGraph(nodes, edges));
    await updateCanvas(canvasId, graph);
    appendLog("Canvas saved");
  }, [canvasId, nodes, edges, appendLog]);

  const listenToRun = useCallback(
    (id: string) => {
      const es = new EventSource(runEventsUrl(id));
      es.onmessage = async (msg) => {
        try {
          const event = JSON.parse(msg.data) as Record<string, unknown>;

          if (event.type === "token" && typeof event.block_id === "string") {
            appendNodeToken(event.block_id, String(event.token ?? ""));
          }

          if (event.type === "block_status" && typeof event.block_id === "string") {
            updateNodeStatus(event.block_id, event.status as "idle" | "running" | "complete" | "error");
          }

          if (event.type === "block_complete" && typeof event.block_id === "string") {
            const output = event.output as {
              content?: string;
              artifact_id?: string;
              file_artifact_id?: string;
            };
            let preview = output?.content?.slice(0, 2000);
            if (!preview && output?.artifact_id) {
              try {
                const full = await getBlockOutput(id, event.block_id);
                preview = full.content?.slice(0, 2000) ?? "";
              } catch {
                preview = `(ref ${output.artifact_id})`;
              }
            }
            updateNodeStatus(event.block_id, "complete", {
              outputPreview: preview,
              outputRef: output?.artifact_id,
              fileArtifactId: output?.file_artifact_id,
            });
            if (output?.file_artifact_id) {
              appendLog(
                `PPTX: ${artifactDownloadUrl(id, output.file_artifact_id)}`
              );
            }
          }

        if (event.type === "persona_complete" && typeof event.task_id === "string") {
          const output = event.output as { content?: string } | undefined;
          appendLog(`Persona ${event.task_id}: ${(output?.content ?? "").slice(0, 80)}…`);
        }
        if (event.type === "run_status") {
          setRun(id, String(event.status));
          appendLog(`Run ${event.status}${event.mode ? ` (${event.mode})` : ""}`);
            if (event.status === "complete" || event.status === "error") {
              setRunning(false);
              es.close();
            }
          }
        } catch {
          /* ignore */
        }
      };
      es.onerror = () => {
        appendLog("SSE closed");
        setRunning(false);
        es.close();
      };
    },
    [appendLog, appendNodeToken, setRun, setRunning, updateNodeStatus]
  );

  const runSwarm = async () => {
    setRunning(true);
    resetNodeOutputs();
    clearLog();
    try {
      const run = await startSwarmRun(true);
      setRun(run.id, run.status);
      appendLog(`Swarm started ${run.id} (3 parallel personas)`);
      listenToRun(run.id);
    } catch (e) {
      setRunning(false);
      appendLog(`Swarm failed: ${e instanceof Error ? e.message : String(e)}`);
    }
  };

  const runPipeline = async () => {
    if (!canvasId) {
      appendLog("Start API + worker first (make api, make worker)");
      return;
    }
    try {
      validateCanvasGraph(flowToGraph(nodes, edges));
    } catch (e) {
      appendLog(`Validation: ${e instanceof Error ? e.message : String(e)}`);
      return;
    }
    setRunning(true);
    resetNodeOutputs();
    clearLog();
    try {
      await saveCanvas();
      const run = await startRun(canvasId);
      setRun(run.id, run.status);
      appendLog(`Run started ${run.id}`);
      listenToRun(run.id);
    } catch (e) {
      setRunning(false);
      appendLog(`Run failed: ${e instanceof Error ? e.message : String(e)}`);
    }
  };

  const resumePipeline = async () => {
    if (!runId) return;
    setRunning(true);
    appendLog(`Resuming ${runId}`);
    try {
      await resumeRun(runId);
      listenToRun(runId);
    } catch (e) {
      setRunning(false);
      appendLog(`Resume failed: ${e instanceof Error ? e.message : String(e)}`);
    }
  };

  return (
    <div className="workspace">
      <CanvasToolbar
        nodes={nodes}
        edges={edges}
        onNodesChange={setNodes}
        onRun={runPipeline}
        onSwarm={runSwarm}
        onResume={resumePipeline}
        onSave={saveCanvas}
        running={running}
        runId={runId}
      />
      <div className="workspace__main">
        <WorkflowCanvas
          nodes={nodes}
          edges={edges}
          onNodesChange={setNodes}
          onEdgesChange={setEdges}
          onSelectionChange={(id) => setSelectedNodeId(id)}
          readOnly={running}
        />
        <BlockInspector />
        <PlanningPanel />
        <MarketplacePanel />
        <aside className="workspace__log">
          <h3>Run log</h3>
          <p className="workspace__meta">
            Canvas: {canvasId ?? "—"} · Run: {runId ?? "—"} · {runStatus ?? "idle"}
          </p>
          <ul>
            {log.map((line, i) => (
              <li key={`${i}-${line.slice(0, 24)}`}>{line}</li>
            ))}
          </ul>
        </aside>
      </div>
    </div>
  );
}
