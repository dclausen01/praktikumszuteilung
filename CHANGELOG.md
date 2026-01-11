# Changelog - Praktikumszuteilungs-Tool

## Version 1.2 - Optimierter Zuordnungsalgorithmus

### Wichtigste Änderung: Score-basierte Optimierung
- **Problem**: Der alte Greedy-Algorithmus wies sequenziell zu und konnte bessere Matches verwerfen, wenn eine Lehrkraft ihre Kapazität erreichte
- **Lösung**: Neuer 2-Phasen-Algorithmus:
  1. **Phase 1**: Berechnet ALLE möglichen Schüler-Lehrkraft-Paarungen
  2. **Phase 2**: Iterative Zuteilung mit dynamischen Score-Updates
     - In jeder Iteration: Neuberechnung aller verfügbaren Scores
     - Wählt immer das beste verfügbare Match
     - Berücksichtigt Einrichtungskonsistenz-Bonus dynamisch
     - Respektiert harte Kapazitätsgrenzen (Soll +1)

- **Ergebnis**: Garantiert beste Matches bei Einhaltung der Kapazitätsgrenzen

## Version 1.1 - Verbesserungen

### 1. Fehlertolerantes Geocoding mit PLZ-Fallback
- **Problem**: Rechtschreibfehler in Adressen (z.B. "starße" statt "straße") führten zu "Adresse nicht gefunden"
- **Lösung**:
  - Bei fehlgeschlagener Adress-Geocodierung automatischer Fallback auf PLZ-basierte Suche
  - Funktioniert sowohl bei "nicht gefunden" als auch bei Geocoding-Fehlern
  - Gibt klare Rückmeldung: "→ Fallback: Versuche nur PLZ..."

### 2. Automatisches Rate-Limit-Handling
- **Problem**: Bei >40 API-Anfragen pro Minute wird das OpenRouteService-Limit überschritten
- **Lösung**:
  - Automatische Erkennung von Rate-Limit-Fehlern (HTTP 429)
  - Wartet 60 Sekunden und wiederholt die Anfrage automatisch
  - Bis zu 3 Wiederholungsversuche
  - Fallback auf Luftlinien-Schätzung nach 3 Fehlversuchen
  - Erhöhte Wartezeit zwischen Anfragen: 1.6s (statt 0.05s)

### 3. Harte Kapazitätsgrenzen für Lehrkräfte
- **Problem**: Soll-Anzahl war nur Empfehlung, keine harte Grenze
- **Lösung**:
  - **Harte Obergrenze**: Maximal Soll +1 Betreuungen
  - Lehrkräfte werden nicht mehr zugeteilt, wenn Kapazität erreicht ist
  - Warnung bei Gesamtkapazität < Anzahl Schülerinnen
  - Detaillierte Validierung am Ende mit Status-Report:
    - ✓ Exakte Einhaltung
    - ✓ Abweichung +/-1 (akzeptabel)
    - ⚠️  Unterlast (< Soll-1)
    - ❌ Überlast (> Soll+1) - sollte nicht vorkommen
  - Ausgabe zeigt aktuellen Stand: "✓ Name → Lehrkraft (Score: 123.4, 2/3)"

### 4. Verbesserte Fehlerbehandlung
- Geocoding mit PLZ-Parameter in der assign_praktika-Funktion
- Klare Fehlermeldungen bei fehlgeschlagenen Zuweisungen
- Validierung der Gesamtkapazität vor Start der Zuteilung

## Technische Details

### Geänderte Funktionen:
- `_geocode()`: Neuer Parameter `plz` für Fallback-Geocodierung
- `_get_route_duration()`: Retry-Logik mit Rate-Limit-Erkennung
- `_is_within_capacity()`: Neue Funktion zur Kapazitätsprüfung
- `assign_praktika()`:
  - Integration der Kapazitätsprüfung
  - PLZ-basiertes Geocoding
  - Validierung am Ende

### API-Rate-Limiting:
- Alte Wartezeit: 0.05s → Neue Wartezeit: 1.6s
- Automatische 60s-Pause bei Rate-Limit
- Bis zu 3 Wiederholungsversuche

## Migration

Keine Breaking Changes - die API bleibt kompatibel.

Die Excel-Dateien benötigen keine Änderungen, profitieren aber automatisch von:
- Besserer Fehlertoleranz bei Adresseingaben
- Stabilerer API-Nutzung
- Garantierter Einhaltung von Kapazitätsgrenzen
