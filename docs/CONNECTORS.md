# Connector authoring

Ava connectors follow MCP patterns with a Postgres registry.

## Built-in connectors

- `google_drive` — read files
- `github` — repos and issues
- `slack` — channels and messages

## API

- `GET /connectors` — list installed connectors
- `GET /connectors/discover` — MCP discovery
- `POST /connectors/oauth/connect` — connect (mock in OSS)
- `POST /connectors/fetch` — fetch resource text for downstream blocks

## Canvas

Use a **Connector** block with `config.connector_id` and `config.resource`.

## Marketplace

`GET /marketplace/connectors` — browse catalog (EE publish via `POST /marketplace/publish`).
