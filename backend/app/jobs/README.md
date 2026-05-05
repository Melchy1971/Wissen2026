# Jobs

Laufzeitnahe Hintergrundjobs fuer M4 werden ueber eine einfache persistierte interne Queue abgewickelt.

Aktueller Stand:

- keine externe Worker-Infrastruktur in M4
- `document_import` und `search_index_rebuild` laufen als persistierte Hintergrundjobs
- `FastAPI BackgroundTasks` dienen nur als Trigger fuer den In-Process-Worker
- gemeinsames Polling erfolgt ueber `GET /api/v1/jobs/{job_id}`

Frontend-Vertrag:

- Upload und Admin-Diagnostik verwenden denselben generischen Jobbegriff
- die UI zeigt normalisierte Zustandslabels statt roher Backend-Strings:
	- `In Warteschlange`
	- `Wird verarbeitet`
	- `Abgeschlossen`
	- `Fehlgeschlagen`

Details siehe [docs/m4-background-jobs-decision.md](H:/WissenMai2026/docs/m4-background-jobs-decision.md).