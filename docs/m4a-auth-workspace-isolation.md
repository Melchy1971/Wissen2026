# M4a - Authentifizierung und Workspace-Isolation

Stand: 2026-05-05

Kontext:

- M3a liefert die GUI-Grundstruktur.
- M3b liefert Retrieval mit Workspace-Bezug im bestehenden Datenmodell.
- M3c liefert Chat-API und Chat-Persistenz mit `workspace_id` und `owner_user_id`.
- Das aktuelle System hat vorbereitete `users`- und `workspaces`-Bezuge, vertraut aber noch auf explizite `workspace_id`-Eingaben und hat keine harte Benutzeridentitaet pro Request.

## 1. Architektur

Ziel von M4a ist, dass jede API-Anfrage eindeutig einem authentifizierten Benutzer und einem autorisierten Workspace-Kontext zugeordnet wird.

Architekturprinzipien:

- Authentifizierung und Workspace-Isolation werden serverseitig erzwungen, nicht nur im Frontend modelliert.
- `workspace_id` aus Query oder Request-Body darf nie blind vertraut werden.
- Jeder Request wird aufgeloest zu:
  - `current_user`
  - `current_workspace`
  - `membership`
- API-Handler konsumieren danach nur noch den aufgeloesten Kontext statt frei uebergebener Workspace-Werte.

Empfohlene Schichten:

- `app/services/auth/`
  - Passwortpruefung und Session-Erzeugung
  - Session-Validierung und Ablaufpruefung
- `app/services/workspaces/`
  - Membership-Pruefung
  - Owner/Admin-Regeln
- `app/api/auth.py`
  - Login, Logout, Me
- `app/api/dependencies/auth.py`
  - `get_current_session()`
  - `get_current_user()`
  - `get_current_workspace()`
  - `require_workspace_access()`

Empfohlener Security-Ansatz fuer M4a:

- Lokales Benutzerkonto mit Passwort-Hashing.
- Cookie-basierte Session fuer das Web-Frontend als Default.
- Session-ID nur serverseitig aufloesen; keine fachliche Logik direkt aus dem Cookie ableiten.
- Optional kann spaeter ein JWT fuer nicht-browserbasierte Clients folgen, M4a selbst sollte aber einen einzigen klaren Primary Path haben.

Begruendung fuer Session statt JWT als Primärpfad:

- Das Zielsystem ist lokal und GUI-zentriert.
- Logout und Session-Ablauf sind mit serverseitiger Session einfacher kontrollierbar.
- CSRF-Schutz ist bei Cookie-Flow explizit planbar und sichtbar.
- Ein lokales Wissenssystem braucht in M4a keine verteilte Token-Infrastruktur.

## 2. Scope

In Scope:

- lokales Benutzerkonto
- Login
- Session-basiertes Authentifizierungsmodell als M4a-Primärpfad
- Workspace-Zugriffspruefung
- API-Guards fuer geschuetzte Endpunkte
- Frontend Login Screen
- Logout

Nicht-Scope:

- OAuth
- SSO
- Rollenmodell ueber Owner/Admin hinaus
- externe Identity Provider
- Multi-User-Collaboration-Features
- fein granularisierte Enterprise-Berechtigungen

## 3. Datenmodell und Migrationsplan

M4a baut auf vorhandenen `users` und `workspaces` auf, fuehrt aber die fehlenden Auth- und Membership-Bausteine explizit ein.

### Zieltabellen

#### `users`

Bestehende vorbereitete User-Tabelle wird erweitert um:

- `email` oder `username` als eindeutiger Login-Identifier
- `password_hash`
- `is_active`
- `last_login_at`
- optional `display_name`

Regeln:

- Login-Identifier eindeutig.
- Keine Speicherung von Klartext-Passwoertern.
- Deaktivierte Nutzer duerfen keine Session aufbauen.

#### `workspaces`

Bestehende vorbereitete Workspace-Tabelle wird gehaertet um:

- `name`
- `slug` oder anderer lokaler eindeutiger Identifikator
- `owner_user_id`
- `created_at`
- `updated_at`

Regeln:

- Jeder Workspace hat genau einen Owner.
- Owner ist immer auch implizit zugriffsberechtigt.

#### `workspace_memberships`

Neue Tabelle fuer explizite Zugriffszuordnung:

- `id`
- `workspace_id`
- `user_id`
- `role` mit minimalen Werten `owner`, `admin`, `member`
- `created_at`
- `updated_at`

Minimalregel fuer M4a:

- Owner/Admin reichen als Modellobergrenze.
- Keine Enterprise-Rollen, keine feingranularen Permissions.

Empfohlene Constraints:

- Unique Constraint auf `(workspace_id, user_id)`
- Check Constraint fuer erlaubte Rollenwerte
- Foreign Keys auf `workspaces.id` und `users.id`

#### `auth_sessions`

Neue Tabelle fuer serverseitige Login-Sessions:

- `id`
- `user_id`
- `expires_at`
- `created_at`
- `last_seen_at`
- `csrf_token_hash` oder getrennte Anti-CSRF-Ablage, falls Cookie-Session mit CSRF-Token umgesetzt wird
- optional `user_agent`
- optional `ip_address`
- optional `revoked_at`

Regeln:

- Nur nicht abgelaufene und nicht widerrufene Sessions gelten.
- Logout widerruft oder loescht die Session serverseitig.

### Migrationsreihenfolge

1. `users` um Login-Identifier, Passwort-Hash und Aktivstatus erweitern.
2. `workspaces` um Owner- und Identifikatorfelder haerten, falls noch nicht vorhanden.
3. Tabelle `workspace_memberships` anlegen.
4. Tabelle `auth_sessions` anlegen.
5. Default-Bestandsdaten backfillen:
   - existierender Default-User bekommt eindeutigen Login-Identifier
   - existierender Default-Workspace bekommt Owner-Zuordnung
   - passende Owner-Membership wird erzeugt
6. Dokument-, Chat- und spaetere Query-Pfade bleiben auf bestehenden `workspace_id`-Feldern, werden aber kuenftig ueber Membership und Request-Kontext abgesichert.

### Migrationsrisiken

- Legacy-Datensaetze ohne saubere Owner-Zuordnung muessen deterministisch einem lokalen Default-Owner zugeordnet werden.
- Bestehende Tests mit hart codierter `workspace_id` muessen auf den neuen Auth-Kontext umgestellt werden.
- Session-Tabellen duerfen SQLite-Tests nicht unnötig verkomplizieren; die Kernregeln muessen auf beiden Test-Backends pruefbar bleiben.

## 4. API-Vertrag

### `POST /auth/login`

Zweck:

- Benutzer authentifizieren und serverseitige Session aufbauen.

Request:

```json
{
  "login": "local-admin",
  "password": "secret"
}
```

Antwort `200`:

```json
{
  "user": {
    "id": "user-1",
    "login": "local-admin",
    "display_name": "Local Admin"
  },
  "memberships": [
    {
      "workspace_id": "ws-1",
      "role": "owner"
    }
  ],
  "active_workspace_id": "ws-1"
}
```

Verhalten:

- Session-Cookie wird serverseitig gesetzt.
- Cookie ist `HttpOnly` und `SameSite=Lax` oder strenger, solange der lokale Produktfluss nicht mehr benoetigt.
- Bei Cookie-basiertem Flow wird ein CSRF-Mechanismus fuer mutierende Requests vorgesehen.

Fehler:

| Status | Code | Bedeutung |
|---:|---|---|
| `401` | `AUTH_INVALID_CREDENTIALS` | Login oder Passwort falsch |
| `403` | `AUTH_USER_DISABLED` | Benutzer ist deaktiviert |
| `422` | `AUTH_LOGIN_INVALID` | Request unvollstaendig oder ungueltig |
| `503` | `SERVICE_UNAVAILABLE` | Auth-Service oder Datenbank nicht verfuegbar |

### `POST /auth/logout`

Zweck:

- Aktive Session beenden.

Request:

- kein Body erforderlich

Antwort `204`:

- Session serverseitig widerrufen oder geloescht
- Session-Cookie entfernt

Fehler:

| Status | Code | Bedeutung |
|---:|---|---|
| `401` | `AUTH_REQUIRED` | keine gueltige Session vorhanden |

### `GET /auth/me`

Zweck:

- Aktuellen Benutzer und seinen autorisierten Workspace-Kontext aufloesen.

Antwort `200`:

```json
{
  "user": {
    "id": "user-1",
    "login": "local-admin",
    "display_name": "Local Admin"
  },
  "memberships": [
    {
      "workspace_id": "ws-1",
      "role": "owner"
    },
    {
      "workspace_id": "ws-2",
      "role": "member"
    }
  ],
  "active_workspace_id": "ws-1"
}
```

Fehler:

| Status | Code | Bedeutung |
|---:|---|---|
| `401` | `AUTH_REQUIRED` | keine gueltige Session |
| `419` oder `401` | `AUTH_SESSION_EXPIRED` | Session abgelaufen |

### API-Guard-Regeln fuer Fachendpunkte

- Geschuetzte Endpunkte lesen den Benutzerkontext aus Session und Membership, nicht aus freier Client-Angabe.
- `workspace_id` aus Query oder Body ist nur noch ein Vorschlag fuer Kontextwahl und muss gegen Membership geprueft werden.
- Wenn kein Zugriff auf den angeforderten Workspace besteht:

| Status | Code | Bedeutung |
|---:|---|---|
| `403` | `WORKSPACE_ACCESS_FORBIDDEN` | Benutzer ist nicht Mitglied des Workspaces |

- Wenn kein Login vorliegt:

| Status | Code | Bedeutung |
|---:|---|---|
| `401` | `AUTH_REQUIRED` | Session fehlt oder ist ungueltig |

## 5. Security-Entscheidungen

### Passwort-Hashing

- Passwort-Hashing mit einem etablierten Verfahren wie Argon2id oder bcrypt.
- Keine selbstgebauten Hash-Loesungen.
- Hash-Konfiguration muss versionierbar und spaeter migrierbar sein.

Praeferenz:

- Argon2id als erster Kandidat fuer neues lokales System.

### Session-Ablauf

- Absolute Session-Laufzeit definieren, z.B. 8-24 Stunden fuer lokale interaktive Nutzung.
- Optionale Sliding Expiration nur kontrolliert und dokumentiert.
- Abgelaufene Sessions muessen serverseitig abgewiesen werden.

### CSRF und CORS

- Bei Cookie-basierten Sessions ist CSRF fuer mutierende Endpunkte verpflichtend zu pruefen.
- `POST /auth/login` und `POST /auth/logout` muessen explizit in das Schutzkonzept eingeordnet werden.
- CORS bleibt fuer lokalen Betrieb restriktiv und erlaubt nur definierte lokale Origins.
- Kein pauschales `allow_origins=["*"]` in M4a.

### Workspace-Kontext

- `workspace_id` wird nie blind aus dem Request uebernommen.
- Server loest immer zuerst `current_user` und Membership auf.
- Danach wird geprueft, ob der Nutzer den angeforderten Workspace ueberhaupt sehen darf.
- Fachservices erhalten nur bereits validierte Kontexte oder Workspace-IDs.

## 6. Frontend-Vertrag

### Login Screen

M4a fuehrt einen dedizierten Login Screen ein mit:

- Login-Identifier
- Passwort
- sichtbare Fehlermeldung bei falschem Login
- Weiterleitung in den zuletzt oder standardmaessig aktiven Workspace nach erfolgreichem Login

### Logout

- Sichtbare Logout-Aktion in der App-Shell.
- Nach Logout Rueckkehr zum Login Screen.
- Geschuetzte Seiten duerfen ohne Session nicht rendern, sondern muessen in den Auth-Flow umleiten.

### Workspace-Kontext im Frontend

- Frontend darf den aktiven Workspace aus `GET /auth/me` oder aus dedizierter Session-State-Antwort ableiten.
- Frontend darf keine freie Workspace-Wahl ohne serverseitige Membership-Pruefung als vertrauenswuerdig behandeln.

## 7. Tests

Pflichttests fuer M4a:

### Backend API

- Login erfolgreich
  - gueltige Credentials erzeugen Session und liefern Benutzerkontext
- Login falsch
  - ungueltige Credentials liefern `401 AUTH_INVALID_CREDENTIALS`
- Zugriff auf fremden Workspace verboten
  - Request mit gueltiger Session, aber ohne Membership liefert `403 WORKSPACE_ACCESS_FORBIDDEN`
- Zugriff ohne Login verboten
  - geschuetzter Endpunkt ohne Session liefert `401 AUTH_REQUIRED`

### Backend Security

- Session-Ablauf wird erzwungen
- Logout invalidiert die Session
- Deaktivierter Benutzer kann sich nicht einloggen
- `workspace_id` aus Request wird nicht ohne Membership akzeptiert

### Frontend

- Login Screen rendert und sendet Login Request
- Fehlerzustand bei falschem Login ist sichtbar
- Logout leert den Client-Auth-Zustand
- Geschuetzte Route ohne Session leitet auf Login um

## 8. Akzeptanzkriterien

- Jede geschuetzte API-Anfrage ist einem authentifizierten Benutzer zugeordnet.
- Jeder fachliche Zugriff ist an einen autorisierten Workspace gebunden.
- Der Server vertraut keiner freien `workspace_id`, ohne Membership und Kontext zu pruefen.
- Login, Logout und `GET /auth/me` sind ueber API und Frontend nutzbar.
- Falscher Login wird sauber abgewiesen.
- Zugriff auf fremde Workspaces wird sauber verboten.
- Zugriff ohne Login wird sauber verboten.

## 9. Risiken

- Zu frueh JWT und Session parallel einzufuehren verdoppelt die Komplexitaet ohne Produktnutzen.
- Membership-Regeln nur im Frontend oder nur in einzelnen Endpunkten zu pruefen fuehrt zu inkonsistenter Isolation.
- CSRF bei Cookie-Sessions zu ignorieren oeffnet unnötige lokale Angriffspfade.
- Legacy-Daten ohne klare Owner-/Membership-Zuordnung koennen Migration und Tests brechen.
- Ein zu breites Rollenmodell in M4a zieht unnoetig Enterprise-Komplexitaet vor.