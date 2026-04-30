# ADR 0002: V1-Scope, Nicht-Ziele und vorbereitete Mehrbenutzerfaehigkeit

## Status

Angenommen.

## Kontext

Die Wissensbasis V1 ist als bewusst begrenzte erste Produktstufe definiert. Sie soll einen klaren Nutzwert fuer einen einzelnen Nutzer liefern, ohne Architekturentscheidungen zu treffen, die spaetere Remote- oder Mehrbenutzerfaehigkeit unnoetig erschweren.

Dabei gelten folgende Rahmenbedingungen:

- V1 ist Single-User.
- Authentifizierung wird in V1 nicht implementiert.
- Das Datenmodell enthaelt vorbereitende Felder `workspace_id` und `owner_user_id`.
- Dokumente werden versioniert.
- Originaldateien werden nicht gespeichert.
- Markdown ist die kanonische Textquelle nach Verarbeitung.
- Chat darf allgemein antworten, muss aber einen Wissensbasisbezug kenntlich machen, wenn keiner vorliegt.
- Dokumentbasierte Antworten muessen Quellen angeben.
- Vektorsuche ist kein Pflichtbestandteil von V1.

Die ADR legt fest, was V1 zwingend enthalten muss, was V1 ausschliessen muss und nach welchen Kriterien spaetere Erweiterungen beurteilt werden.

## Muss in V1

Die V1-Wissensbasis muss die folgenden Eigenschaften erfuellen:

1. Das System muss als Single-User-System betrieben werden koennen.
2. Das Datenmodell muss vorbereitende Felder `workspace_id` und `owner_user_id` enthalten duerfen oder vorsehen, ohne daraus aktive Mehrbenutzerlogik abzuleiten.
3. Importierte Inhalte muessen in eine kanonische Markdown-Repraesentation ueberfuehrt werden.
4. Dokumentinhalte muessen versioniert werden, sodass inhaltliche Aenderungen nachvollziehbar bleiben.
5. Dokumentbasierte Antworten muessen Quellen referenzieren.
6. Chat-Antworten duerfen allgemeines Weltwissen verwenden, muessen aber kenntlich machen, wenn eine Antwort nicht auf Inhalten der Wissensbasis beruht.
7. Die Persistenz darf abgeleitete Inhalte, Metadaten, Versionen und Suchgrundlagen speichern, aber nicht die Originaldatei als fuehrende Quelle.

## Nicht in V1

Die V1-Wissensbasis darf die folgenden Eigenschaften nicht enthalten oder voraussetzen:

1. Es darf keine Authentifizierung implementiert werden.
2. Es darf keine aktive Rollenlogik implementiert werden.
3. Es darf keine Rechtepruefung oder Mandantenpruefung geben.
4. Es duerfen keine Originaldateien als fachlich fuehrende oder dauerhaft gespeicherte Quelle abgelegt werden.
5. Es darf keine Vektorsuche als notwendige Voraussetzung fuer den V1-Betrieb geben.
6. Es darf keine fachliche Entscheidung vorweggenommen werden, die ausschliesslich fuer spaetere Mehrbenutzer- oder Remote-Szenarien relevant ist und fuer V1 keinen direkten Nutzen liefert.

## Vorbereitete spaetere Faehigkeiten

Die folgenden Punkte sind in V1 vorbereitet, aber nicht aktiviert oder fachlich ausgebaut:

- `workspace_id` bereitet eine spaetere logische Trennung von Arbeitsraeumen vor.
- `owner_user_id` bereitet eine spaetere eindeutige Zuordnung von Inhalten zu einem Nutzer oder Ersteller vor.
- Die Trennung zwischen lokaler GUI, Backend und remote Datenbank bereitet spaetere Remote-Betriebsformen vor.
- Das Provider-Interface fuer KI bereitet spaetere austauschbare lokale oder externe Modelle vor.

Diese Vorbereitung ist nur zulaessig, wenn sie keine der folgenden Nebenwirkungen erzeugt:

- keine aktive Rechteauswertung,
- keine Benutzerverwaltung,
- keine Rollensemantik,
- keine Pflicht zu zusaetzlicher Betriebsinfrastruktur.

## Scope-Risiken

Die folgenden Risiken koennen zu Scope Creep oder fachlicher Unklarheit fuehren:

- Vorbereitete Felder wie `workspace_id` oder `owner_user_id` werden spaeter faelschlich als bestehende Mehrbenutzerunterstuetzung interpretiert.
- Eine allgemeine Chat-Antwort ohne klare Kennzeichnung wird als dokumentgestuetzte Aussage missverstanden.
- Quellenpflicht wird inkonsistent umgesetzt und verwischt dadurch die Grenze zwischen Wissensbasisinhalt und allgemeinem Modellwissen.
- Die Einfuehrung optionaler Suchtechniken wird spaeter stillschweigend zu einer impliziten V1-Pflicht erweitert.
- Die Nicht-Speicherung von Originaldateien wird durch Debug-, Backup- oder Komfortpfade unbeabsichtigt unterlaufen.

## Entscheidungskriterien fuer spaetere Erweiterungen

Eine spaetere Erweiterung ausserhalb von V1 darf erst beschlossen werden, wenn alle folgenden Fragen positiv beantwortet oder bewusst verneint dokumentiert wurden:

1. Liefert die Erweiterung einen direkten fachlichen Nutzen, der im Single-User-V1 nicht bereits ausreichend abgedeckt ist?
2. Erhoeht die Erweiterung die Komplexitaet von Betrieb, Datenmodell oder UI nur in vertretbarem Mass?
3. Kann die Erweiterung eingefuehrt werden, ohne bestehende V1-Regeln zu Auth, Rollen, Originaldateien oder Quellenpflicht stillschweigend aufzuweichen?
4. Ist klar dokumentiert, ob die Erweiterung optional, Standard oder verpflichtend wird?
5. Ist nachvollziehbar beschrieben, wie sich die Erweiterung auf Datenmigration, API-Vertrag und Benutzererwartung auswirkt?

## Risiken der Entscheidung

- Die bewusste Nicht-Implementierung von Auth und Rechten vereinfacht V1, schraenkt aber den Einsatzbereich absichtlich auf kontrollierte Nutzungsszenarien ein.
- Die Vorbereitung von spaeteren Mehrbenutzerfeldern schafft Zukunftsfaehigkeit, erfordert aber disziplinierte Kommunikation, damit kein falscher Funktionsumfang angenommen wird.
- Die strikte Ablehnung der Originaldateispeicherung vereinfacht die fachliche Fuehrung des Systems, kann aber spaeter Zusatzentscheidungen fuer Nachvollziehbarkeit und Importdiagnostik erforderlich machen.

## Nicht-Ziele

- Kein Login, keine Session- oder Token-Mechanik.
- Keine Rollen, keine Rechteprofile, keine Zugriffsmatrix.
- Keine Mandantentrennung im laufenden Verhalten.
- Keine Speicherung von Originaldateien als Referenzarchiv.
- Keine Festlegung, dass Vektorsuche in V1 vorhanden oder notwendig sein muss.
- Keine Vorentscheidung fuer spaetere Organisations- oder Teamfunktionen.