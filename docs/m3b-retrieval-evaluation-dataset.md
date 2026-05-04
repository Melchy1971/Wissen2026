# M3b - Retrieval Evaluation Dataset

Stand: 2026-05-04

Zweck:

- Die Suchqualitaet von M3b soll mit einem kleinen, stabilen Gold-Set messbar werden.
- Das Dataset bewertet bewusst nur die aktuelle Retrieval-Stufe: keyword-basierte Chunk-Suche.
- Chat, semantische Suche, Query-Rewriting und Re-Ranking bleiben ausserhalb dieses Datensatzes.

## 1. Dataset-Struktur

Minimale logische Struktur:

```json
{
  "documents": [
    {
      "document_id": "eval-doc-01",
      "title": "Arbeitsvertrag Hybridmodell",
      "topic": "hr",
      "chunks": [
        {"chunk_id": "eval-doc-01-c01", "label": "Probezeit und Arbeitsort"},
        {"chunk_id": "eval-doc-01-c02", "label": "Kuendigungsfrist"},
        {"chunk_id": "eval-doc-01-c03", "label": "Homeoffice-Regel"}
      ]
    }
  ],
  "queries": [
    {
      "query_id": "q-01",
      "query": "probezeit arbeitsvertrag",
      "expected_relevant_chunks": ["eval-doc-01-c01"],
      "expects_results": true
    }
  ],
  "metrics": ["precision_at_5", "recall_at_10", "mrr", "no_result_accuracy"]
}
```

Minimalregeln:

- Jedes Testdokument hat genau einen stabilen `document_id`.
- Jeder relevante Zieltreffer wird auf Chunk-Ebene ueber `chunk_id` referenziert.
- Queries referenzieren nur Chunks des aktuellen, lesbaren Dokumentbestands.
- Nicht-Treffer-Queries sind explizit erlaubt und fuer `No-result accuracy` notwendig.

## 2. Testdokumente

Das Minimaldataset umfasst 20 Testdokumente mit unterschiedlichen Themen. Jedes Dokument soll in 2 bis 4 Chunks zerlegt werden; die Tabelle benennt nur die zentralen Gold-Chunks.

| Dokument | Titel | Thema | Relevante Chunk-IDs | Inhaltlicher Fokus |
|---|---|---|---|---|
| `eval-doc-01` | Arbeitsvertrag Hybridmodell | HR / Recht | `eval-doc-01-c01`, `eval-doc-01-c02`, `eval-doc-01-c03` | Probezeit, Kuendigungsfrist, Homeoffice |
| `eval-doc-02` | Reisekostenrichtlinie 2026 | Finance / HR | `eval-doc-02-c01`, `eval-doc-02-c02` | Kilometerpauschale, Hotelgrenze |
| `eval-doc-03` | Datenschutzleitlinie Kundenservice | Datenschutz | `eval-doc-03-c01`, `eval-doc-03-c03` | Aufbewahrungsdauer, Zugriffskontrolle |
| `eval-doc-04` | Incident Runbook API-Ausfall | IT Operations | `eval-doc-04-c01`, `eval-doc-04-c02`, `eval-doc-04-c03` | Alarmierung, Rollback, Statusseite |
| `eval-doc-05` | Produktblatt Solardach S1 | Produkt | `eval-doc-05-c01`, `eval-doc-05-c02` | Leistung, Garantie |
| `eval-doc-06` | Wartungsplan Produktionslinie A | Produktion | `eval-doc-06-c01`, `eval-doc-06-c03` | Inspektionsintervall, Schmierstoff |
| `eval-doc-07` | Sicherheitsunterweisung Lager | Sicherheit | `eval-doc-07-c01`, `eval-doc-07-c02` | Stapler, Schutzkleidung |
| `eval-doc-08` | Onboarding Checkliste Entwickler | Engineering | `eval-doc-08-c01`, `eval-doc-08-c02`, `eval-doc-08-c03` | Repo-Zugang, Laptop, VPN |
| `eval-doc-09` | Architekturentscheidung PostgreSQL FTS | Architektur | `eval-doc-09-c01`, `eval-doc-09-c02` | GIN-Index, Ranking-Baseline |
| `eval-doc-10` | Kundenangebot ERP-Einfuehrung | Sales | `eval-doc-10-c01`, `eval-doc-10-c03` | Projektphasen, Zahlungsplan |
| `eval-doc-11` | Meeting-Protokoll Standortwechsel | Management | `eval-doc-11-c01`, `eval-doc-11-c02` | Umzugstermin, Budget |
| `eval-doc-12` | FAQ Firmenwagen | HR / Policy | `eval-doc-12-c01`, `eval-doc-12-c02` | private Nutzung, Tankkarte |
| `eval-doc-13` | Liefervertrag Verpackungsmaterial | Einkauf | `eval-doc-13-c01`, `eval-doc-13-c03` | Mindestabnahme, Lieferfrist |
| `eval-doc-14` | Support-Handbuch Passwort-Reset | IT Support | `eval-doc-14-c01`, `eval-doc-14-c02` | MFA, Self-Service Reset |
| `eval-doc-15` | Nachhaltigkeitsbericht Emissionen | ESG | `eval-doc-15-c01`, `eval-doc-15-c02` | Scope-1, Reduktionsziel |
| `eval-doc-16` | Schulungsunterlage Erste Hilfe | Sicherheit | `eval-doc-16-c01`, `eval-doc-16-c03` | Notruf, stabile Seitenlage |
| `eval-doc-17` | Preisliste Wartungsvertraege | Service | `eval-doc-17-c01`, `eval-doc-17-c02` | Bronze/Silber/Gold, Reaktionszeit |
| `eval-doc-18` | API Guideline Fehlermodell | Engineering | `eval-doc-18-c01`, `eval-doc-18-c02` | Fehlercodes, JSON-Envelope |
| `eval-doc-19` | Marketingplan Fruehjahrskampagne | Marketing | `eval-doc-19-c01`, `eval-doc-19-c03` | Zielgruppe, Budgetkanal |
| `eval-doc-20` | Notfallplan Stromausfall Werk | Operations | `eval-doc-20-c01`, `eval-doc-20-c02`, `eval-doc-20-c03` | Generatorstart, Eskalation, Evakuierung |

## 3. Beispiel-Daten

Beispiel fuer drei Dokumente mit Gold-Chunks:

```yaml
documents:
  - document_id: eval-doc-01
    title: Arbeitsvertrag Hybridmodell
    topic: hr
    chunks:
      - chunk_id: eval-doc-01-c01
        text: "Die Probezeit betraegt sechs Monate. Der regelmaessige Arbeitsort ist Berlin, mobiles Arbeiten ist an zwei Tagen pro Woche moeglich."
      - chunk_id: eval-doc-01-c02
        text: "Nach der Probezeit gilt eine Kuendigungsfrist von vier Wochen zum Fuenfzehnten oder zum Monatsende."
      - chunk_id: eval-doc-01-c03
        text: "Homeoffice ist nach Abstimmung mit der Fuehrungskraft moeglich, sofern Datenschutz und Erreichbarkeit sichergestellt sind."

  - document_id: eval-doc-09
    title: Architekturentscheidung PostgreSQL FTS
    topic: architecture
    chunks:
      - chunk_id: eval-doc-09-c01
        text: "Die Suche basiert auf PostgreSQL Full Text Search. Ein GIN-Index auf search_vector beschleunigt die Kandidatenselektion."
      - chunk_id: eval-doc-09-c02
        text: "Die Ranking-Baseline nutzt ts_rank. Bei Score-Gleichstand entscheidet created_at vor chunk_index."

  - document_id: eval-doc-18
    title: API Guideline Fehlermodell
    topic: engineering
    chunks:
      - chunk_id: eval-doc-18-c01
        text: "API-Fehler werden als JSON-Envelope mit code, message und details ausgeliefert."
      - chunk_id: eval-doc-18-c02
        text: "ServiceUnavailable wird mit HTTP 503 und dem Fehlercode SERVICE_UNAVAILABLE ausgeliefert."
```

## 4. Suchqueries

Das Minimaldataset umfasst 30 Queries. Davon sind 26 positive Queries mit mindestens einem erwarteten Treffer und 4 negative Queries ohne erwarteten Treffer.

| Query-ID | Query | Erwartete relevante Chunks | Erwartet Treffer |
|---|---|---|---:|
| `q-01` | `probezeit arbeitsvertrag` | `eval-doc-01-c01` | ja |
| `q-02` | `kuendigungsfrist monatsende` | `eval-doc-01-c02` | ja |
| `q-03` | `homeoffice regelung datenschutz` | `eval-doc-01-c03` | ja |
| `q-04` | `kilometerpauschale dienstreise` | `eval-doc-02-c01` | ja |
| `q-05` | `hotelkosten obergrenze` | `eval-doc-02-c02` | ja |
| `q-06` | `aufbewahrungsdauer kundendaten` | `eval-doc-03-c01` | ja |
| `q-07` | `zugriffskontrolle kundenservice` | `eval-doc-03-c03` | ja |
| `q-08` | `api ausfall rollback` | `eval-doc-04-c02` | ja |
| `q-09` | `statusseite incident kommunikation` | `eval-doc-04-c03` | ja |
| `q-10` | `solardach garantie jahre` | `eval-doc-05-c02` | ja |
| `q-11` | `wartungsintervall produktionslinie` | `eval-doc-06-c01` | ja |
| `q-12` | `schutzkleidung lager` | `eval-doc-07-c02` | ja |
| `q-13` | `vpn zugang onboarding` | `eval-doc-08-c03` | ja |
| `q-14` | `gin index search vector` | `eval-doc-09-c01` | ja |
| `q-15` | `ts_rank tie breaker chunk index` | `eval-doc-09-c02` | ja |
| `q-16` | `zahlungsplan erp angebot` | `eval-doc-10-c03` | ja |
| `q-17` | `umzugstermin standortwechsel` | `eval-doc-11-c01` | ja |
| `q-18` | `tankkarte private nutzung` | `eval-doc-12-c02` | ja |
| `q-19` | `mindestabnahme verpackungsmaterial` | `eval-doc-13-c01` | ja |
| `q-20` | `passwort reset mfa` | `eval-doc-14-c01`, `eval-doc-14-c02` | ja |
| `q-21` | `scope 1 emissionen` | `eval-doc-15-c01` | ja |
| `q-22` | `stabile seitenlage notruf` | `eval-doc-16-c01`, `eval-doc-16-c03` | ja |
| `q-23` | `reaktionszeit gold vertrag` | `eval-doc-17-c02` | ja |
| `q-24` | `service unavailable json envelope` | `eval-doc-18-c01`, `eval-doc-18-c02` | ja |
| `q-25` | `zielgruppe fruehjahrskampagne` | `eval-doc-19-c01` | ja |
| `q-26` | `generatorstart stromausfall` | `eval-doc-20-c01` | ja |
| `q-27` | `kaffeebohnen procurement` | - | nein |
| `q-28` | `urlaubskalender kindergarten` | - | nein |
| `q-29` | `3d drucker filamente` | - | nein |
| `q-30` | `kantinenplan august` | - | nein |

Ergaenzung fuer `No-result accuracy`:

- Fuer das Minimaldataset sollten spaeter weitere No-Hit-Queries vorbereitet werden, sobald M3b in einen staerkeren Regressionstest uebergeht.
- Fuer den Start reicht die kleine Negativmenge, um die Metrik ueberhaupt sichtbar zu machen; fuer belastbarere Trends sollte sie spaeter vergroessert werden.

## 5. Bewertungsmethodik

### Precision@5

Frage:

- Wie viele der ersten 5 Treffer sind relevant?

Definition pro Query:

$$
Precision@5 = \frac{\text{relevante Treffer in Top 5}}{\min(5, \text{Anzahl gelieferter Treffer})}
$$

Praxisregel fuer M3b:

- Wenn weniger als 5 Treffer geliefert werden, wird gegen die gelieferte Trefferanzahl normiert.
- Negative Queries mit korrektem Leerresultat gehen nicht in `Precision@5` ein, sondern in `No-result accuracy`.

### Recall@10

Frage:

- Wie viele der erwarteten relevanten Chunks werden in den ersten 10 Treffern gefunden?

Definition pro Query:

$$
Recall@10 = \frac{\text{relevante Treffer in Top 10}}{\text{Anzahl erwarteter relevanter Chunks}}
$$

### MRR

Frage:

- Wie frueh taucht der erste relevante Treffer auf?

Definition:

$$
MRR = \frac{1}{|Q_{pos}|} \sum_{q \in Q_{pos}} \frac{1}{rank_q}
$$

mit `rank_q` als Position des ersten relevanten Treffers fuer positive Queries.

### No-result accuracy

Frage:

- Wie oft liefert die Suche fuer Queries ohne Gold-Treffer korrekt ein leeres Ergebnis?

Definition:

$$
NoResultAccuracy = \frac{\text{korrekt leere Antworten fuer No-Hit-Queries}}{\text{Anzahl No-Hit-Queries}}
$$

## 6. Zielwerte fuer M3b

Die Zielwerte muessen zur aktuellen M3b-Stufe passen: PostgreSQL FTS, kein semantisches Retrieval, kein Re-Ranking.

| Metrik | Zielwert M3b | Bedeutung |
|---|---:|---|
| `Precision@5` | `>= 0.60` | Mindestens 3 von 5 fruehen Treffern sollen im Mittel relevant sein. |
| `Recall@10` | `>= 0.80` | Die meisten Gold-Chunks sollen in den ersten 10 Treffern auftauchen. |
| `MRR` | `>= 0.75` | Der erste relevante Treffer soll haeufig in Position 1 oder 2 liegen. |
| `No-result accuracy` | `>= 0.95` | No-Hit-Queries duerfen fast nie Phantomtreffer liefern. |

Interpretation:

- `Precision@5` darf fuer M3b moderat sein, weil noch kein Re-Ranking existiert.
- `Recall@10` ist fuer M3b wichtiger als perfekte Precision, da die Retrieval-Basis zuerst robuste Kandidaten liefern muss.
- `No-result accuracy` muss hoch sein, um fachlich falsche Treffer bei leeren Suchraeumen zu verhindern.

## 7. Minimale Auswertung

Empfohlener Auswertungsablauf:

1. Alle 30 Queries gegen denselben stabilen Testbestand ausfuehren.
2. Trefferlisten pro Query mit `chunk_id` und `rank` speichern.
3. Treffer gegen das Gold-Set `expected_relevant_chunks` matchen.
4. `Precision@5`, `Recall@10`, `MRR` und `No-result accuracy` berechnen.
5. Ergebnisse pro Query und aggregiert dokumentieren.

Minimale Ergebnisstruktur:

```json
{
  "run_id": "m3b-eval-001",
  "metrics": {
    "precision_at_5": 0.67,
    "recall_at_10": 0.83,
    "mrr": 0.79,
    "no_result_accuracy": 1.0
  },
  "per_query": [
    {
      "query_id": "q-14",
      "query": "gin index search vector",
      "returned_chunk_ids": ["eval-doc-09-c01", "eval-doc-18-c01"],
      "expected_relevant_chunks": ["eval-doc-09-c01"],
      "precision_at_5": 0.5,
      "recall_at_10": 1.0,
      "reciprocal_rank": 1.0
    }
  ]
}
```

## 8. Abgrenzung

Dieses Minimaldataset misst nur die Retrieval-Qualitaet auf Chunk-Ebene.

Explizit nicht Teil der M3b-Evaluation:

- semantische Relevanz ohne lexikalische Uebereinstimmung
- Antwortqualitaet eines Chat- oder QA-Systems
- Cross-Encoder- oder LLM-Re-Ranking
- Benutzerpersonalisierung
- Query-Vorschlaege, Facetten oder gespeicherte Suchen