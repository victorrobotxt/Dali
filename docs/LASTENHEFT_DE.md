# LASTENHEFT: Projekt Glashaus
**Version:** 1.0.0
**Status:** In Entwicklung

## 1. Einleitung
Das Projekt "Glashaus" ist eine automatisierte Due-Diligence-Plattform für den Immobilienmarkt in Sofia. Ziel ist die Beseitigung von Informationsasymmetrien durch den Einsatz von OSINT und KI-gestützter Datenanalyse.

## 2. Ist-Zustand (Problemstellung)
- **Datenfragmentierung:** Grundbuch (Registry), Kataster (Cadastre) und Gemeinde agieren in Silos.
- **Intransparenz:** Immobilienanzeigen enthalten oft ungenaue Flächenangaben und verschleierte Adressen.
- **Prozessineffizienz:** Manuelle Prüfungen sind teuer und langsam.

## 3. Soll-Zustand (Lösung)
Ein Microservices-System, das folgende Kernfunktionen bietet:
1.  **Automatische Adress-Deduktion:** Ermittlung der exakten Adresse aus unstrukturierten Anzeigentexten und Bildern.
2.  **Soll/Ist-Abgleich:** Automatischer Vergleich von Maklerangaben (Anzeige) mit amtlichen Katasterdaten.
3.  **Risikobewertung:** Algorithmische Berechnung eines "Risk Scores" (0-100).

## 4. Technische Anforderungen
- **Architektur:** Event-Driven Microservices (Python/FastAPI).
- **Datenbank:** PostgreSQL mit PostGIS für Geodatenverarbeitung.
- **KI-Integration:**
    - *Tier 1:* Textanalyse (Low Cost / Gemini Flash).
    - *Tier 2:* Visuelle Analyse (High Cost / Gemini Pro).

## 5. Nicht-funktionale Anforderungen
- **Idempotenz:** Wiederholte Uploads dürfen keine Datenkorruption verursachen.
- **Skalierbarkeit:** Das System muss Warteschlangen (Queues) nutzen, um Lastspitzen bei Scrapern abzufangen.
