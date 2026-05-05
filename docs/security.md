# Security

Stand: 2026-05-05

## M4a Auth- und Workspace-Konsistenz

Der dokumentierte Zielzustand fuer M4a ist ein serverseitig erzwungener Benutzer- und Workspace-Kontext. Dieser Zielzustand ist im aktuellen Code nur teilweise umgesetzt.

Nachweisbar implementiert:

- einheitliches API-Fehlerformat
- Fehlercodes `AUTH_REQUIRED`, `ADMIN_REQUIRED`, `WORKSPACE_REQUIRED`
- Admin-Schutz fuer `POST /api/v1/admin/search-index/rebuild` ueber `x-admin-token`
- serverseitig gesetzter Default-Kontext fuer `POST /documents/import`
- Workspace-Filter in Dokument-, Search- und Chat-Vertraegen

Nicht nachweisbar implementiert:

- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`
- Cookie-Session oder JWT-Flow fuer regulare Fachendpunkte
- `workspace_memberships`
- `auth_sessions`
- serverseitige Membership-Pruefung fuer Dokument-, Search- und Chat-Endpunkte
- CSRF-Schutz fuer mutierende Cookie-basierte Requests

## Auth-Modell im aktuellen Stand

- Regulare Benutzer-Authentifizierung ist im Code nicht nachweisbar.
- Der einzige klar geschuetzte Endpoint ist der Admin-Rebuild mit `x-admin-token`.
- Uploads laufen weiterhin mit `settings.default_workspace_id` und `settings.default_user_id`.

## Workspace-Isolation im aktuellen Stand

- Dokumente, Chat-Sessions und Search arbeiten fachlich mit `workspace_id`.
- Die Isolation wird aktuell hauptsaechlich ueber explizite `workspace_id`-Parameter oder Default-Kontext modelliert.
- Eine echte serverseitige Autorisierung eines Benutzers gegen einen Workspace ist nicht nachweisbar.

## Betroffene Endpoints

- `GET /documents`
- `POST /documents/import`
- `GET /api/v1/search/chunks`
- `POST /api/v1/chat/sessions`
- `GET /api/v1/chat/sessions`
- `POST /api/v1/chat/sessions/{session_id}/messages`
- `POST /api/v1/admin/search-index/rebuild`

## Fehlercodes

- `AUTH_REQUIRED`: Admin-Token fehlt
- `ADMIN_REQUIRED`: Admin-Token falsch
- `WORKSPACE_REQUIRED`: Workspace-Parameter fehlt im Fachrequest

## Bekannte Einschraenkungen

- Frontend vertraut fuer Dokumente und Chat weiterhin auf `workspace_id` im Query-String.
- Teile der GUI fallen auf einen hart codierten Default-Workspace zurueck.
- Es gibt kein serverseitiges `current_user`/`current_workspace`-Objekt fuer Fachendpunkte.
- Es gibt keine Logout- oder Session-Invalidierungslogik fuer regulare Benutzer.

## Nicht-Scope

- OAuth
- SSO
- externe Identity Provider
- Enterprise-Rollenmodell
- feingranulare Berechtigungen

## Abschlussentscheidung fuer M4a

- Dokumentation aktualisiert: ja
- Sicherheitsmodell konsistent mit einem abgeschlossenen M4a: nein
- Entscheidung: M4a ist im vorliegenden Repository nicht abgeschlossen