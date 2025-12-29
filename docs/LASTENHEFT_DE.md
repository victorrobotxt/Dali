# LASTENHEFT: Projekt Glashaus
**Version:** 1.1.0
**Status:** In Entwicklung

## 1. Einleitung
[span_66](start_span)Das Projekt "Glashaus" ist eine automatisierte Due-Diligence-Plattform für den Immobilienmarkt in Sofia[span_66](end_span). Ziel ist die Beseitigung von Informationsasymmetrien durch den Einsatz von OSINT und multimodaler KI-Analyse.

## 2. Ist-Zustand (Problemstellung)
- **[span_67](start_span)Datenfragmentierung:** Grundbuch (Registry), Kataster (Cadastre) und Gemeinde (NAG) agieren in Silos[span_67](end_span).
- **[span_68](start_span)Intransparenz:** Immobilienanzeigen enthalten oft ungenaue Flächenangaben, "Atelier"-Fallen und verschleierte Adressen[span_68](end_span).
- **Prozessineffizienz:** Manuelle Prüfungen sind teuer und langsam.

## 3. Soll-Zustand (Lösung)
Ein Microservices-System, das folgende Kernfunktionen bietet:
1.  **[span_69](start_span)[span_70](start_span)Automatische Adress-Deduktion:** Ermittlung der exakten Adresse aus unstrukturierten Anzeigentexten und visueller Landmarken-Analyse[span_69](end_span)[span_70](end_span).
2.  **[span_71](start_span)3D-Audit (Unified Forensics):** Gleichzeitige Prüfung von Kataster (Fläche), Gemeinde (Enteignung/Baugenehmigung) und Gesetz (Nutzungsstatus)[span_71](end_span).
3.  **[span_72](start_span)Social Risk Detection:** Analyse der Eigentümerstruktur (Privat vs. Gemeinde) zur Erkennung von "Social Housing"-Risiken[span_72](end_span).
4.  **[span_73](start_span)Risikobewertung:** Algorithmische Berechnung eines "Risk Scores" (0-100)[span_73](end_span).

## 4. Technische Anforderungen
- **[span_74](start_span)Architektur:** Event-Driven Microservices (Python/FastAPI)[span_74](end_span).
- **[span_75](start_span)Datenbank:** PostgreSQL mit PostGIS für Geodatenverarbeitung[span_75](end_span).
- **KI-Integration:**
    - **[span_76](start_span)[span_77](start_span)Multimodal Engine:** Google Gemini 3.0 Flash[span_76](end_span)[span_77](end_span). [span_78](start_span)Verarbeitet Text und Bilder simultan zur Erkennung von visuellen Diskrepanzen (z.B. "Luxus" im Text vs. "Panel" im Bild)[span_78](end_span).

## 5. Nicht-funktionale Anforderungen
- **[span_79](start_span)Idempotenz:** Wiederholte Uploads dürfen keine Datenkorruption verursachen (`content_hash` Prüfungen)[span_79](end_span).
- **[span_80](start_span)Skalierbarkeit:** Das System nutzt Celery/Redis Warteschlangen, um Lastspitzen bei Scrapern abzufangen[span_80](end_span).
