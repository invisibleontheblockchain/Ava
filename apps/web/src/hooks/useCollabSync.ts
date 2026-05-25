"use client";

import { useEffect, useRef } from "react";
import type { Edge, Node } from "@xyflow/react";
import * as Y from "yjs";
import { WebsocketProvider } from "y-websocket";
import { collabWsUrl } from "@/lib/collab";

/** Zustand ↔ Y.js bidirectional sync + awareness (Document 2 §3/4). */
export function useCollabSync(
  roomId: string | null,
  nodes: Node[],
  edges: Edge[],
  setNodes: (nodes: Node[]) => void,
  setEdges: (edges: Edge[]) => void,
  userName = "user",
) {
  const docRef = useRef<Y.Doc | null>(null);
  const applying = useRef(false);

  useEffect(() => {
    const url = roomId ? collabWsUrl(roomId) : null;
    if (!url) return;

    const doc = new Y.Doc();
    docRef.current = doc;
    const provider = new WebsocketProvider(url, roomId!, doc, { connect: true });
    const yNodes = doc.getArray<unknown>("nodes");
    const yEdges = doc.getArray<unknown>("edges");
    const awareness = provider.awareness;

    awareness.setLocalStateField("user", { name: userName, color: "#8b5cf6" });

    const pushLocal = () => {
      if (applying.current) return;
      doc.transact(() => {
        yNodes.delete(0, yNodes.length);
        yNodes.push(nodes as unknown[]);
        yEdges.delete(0, yEdges.length);
        yEdges.push(edges as unknown[]);
      });
    };

    const onRemote = () => {
      applying.current = true;
      const rn = yNodes.toArray() as Node[];
      const re = yEdges.toArray() as Edge[];
      if (rn.length) setNodes(rn);
      if (re.length) setEdges(re);
      applying.current = false;
    };

    yNodes.observe(onRemote);
    yEdges.observe(onRemote);
    pushLocal();

    return () => {
      yNodes.unobserve(onRemote);
      yEdges.unobserve(onRemote);
      provider.destroy();
      doc.destroy();
    };
  }, [roomId, userName, setNodes, setEdges]);

  useEffect(() => {
    if (!docRef.current || !roomId) return;
    const yNodes = docRef.current.getArray<unknown>("nodes");
    const yEdges = docRef.current.getArray<unknown>("edges");
    if (applying.current) return;
    docRef.current.transact(() => {
      yNodes.delete(0, yNodes.length);
      yNodes.push(nodes as unknown[]);
      yEdges.delete(0, yEdges.length);
      yEdges.push(edges as unknown[]);
    });
  }, [nodes, edges, roomId]);
}
