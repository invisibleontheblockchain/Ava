/** Y.js collaboration client stub (Phase 4) — connect when NEXT_PUBLIC_COLLAB_WS_URL is set. */

export function collabWsUrl(roomId: string): string | null {
  const base = process.env.NEXT_PUBLIC_COLLAB_WS_URL;
  if (!base) return null;
  return `${base}/${roomId}`;
}
