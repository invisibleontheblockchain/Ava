/** Y.js collaboration server (Phase 4) */
const http = require("http");
const WebSocket = require("ws");
const { setupWSConnection } = require("y-websocket/bin/utils");

const port = Number(process.env.PORT || 1234);
const server = http.createServer((_req, res) => {
  res.writeHead(200, { "Content-Type": "text/plain" });
  res.end("ava y-websocket");
});
const wss = new WebSocket.Server({ server });
wss.on("connection", setupWSConnection);
server.listen(port, () => console.log(`collab ws://0.0.0.0:${port}`));
