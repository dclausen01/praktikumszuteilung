# Praktikumszuteilungs-Tool

Automatische Zuteilung von Lehrkräften zu Schülerinnen-Praktika basierend auf optimierten Kriterien.

## Features

- **Intelligente Zuteilung** basierend auf:
  1. Klassenübereinstimmung (höchste Priorität)
  2. Fahrzeit-Optimierung via OpenRouteService
  3. Einrichtungskonsistenz (eine Lehrkraft pro Einrichtung bevorzugt)
  4. Lastverteilung gemäß Soll-Anzahl

- **Echte Fahrzeiten** über OpenRouteService API
- **Automatische Geocodierung** von Adressen
- **Excel-basierter Workflow** (Input & Output)
- **Interaktive Bedienung**

## Installation

### 1. Python-Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

### 2. OpenRouteService API-Key besorgen

1. Registrierung (kostenlos): https://openrouteservice.org/dev/#/signup
2. API-Key kopieren
3. In `config.json` eintragen:

```json
{
  "api_key": "HIER_IHREN_API_KEY_EINTRAGEN",
  ...
}
```

## Verwendung

### Input-Dateien vorbereiten

#### Schülerinnen-Datei (Excel)
Erforderliche Spalten:
- `Name` - Name der Schülerin
- `Klasse` - z.B. "FSP23a"
- `Einrichtung` - Name der Praktikumseinrichtung
- `Straße` - Straße und Hausnummer
- `PLZ` - Postleitzahl
- `Ort` - Ortsname

#### Lehrkräfte-Datei (Excel)
Erforderliche Spalten:
- `Name` - Name der Lehrkraft
- `PLZ_Wohnort` - Postleitzahl des Wohnorts
- `Klassen` - Kommaseparierte Liste, z.B. "FSP23a, FSP23b"
- `Soll_Anzahl_Betreuungen` - Anzahl der zu betreuenden Schülerinnen

### Tool ausführen

```bash
python praktikumszuteilung.py
```

Das Tool fragt interaktiv nach den Dateipfaden.

### Output

Die Ergebnisdatei heißt z.B.:
```
Zuteilung_2026_FSP23a_FSP23b.xlsx
```

Sie enthält zwei Sheets:
1. **Zuteilungen** - Vollständige Zuordnung mit Scores und Begründungen
2. **Statistik** - Übersicht pro Lehrkraft

## Scoring-System

Das Tool vergibt Punkte nach folgenden Kriterien:

| Kriterium | Punkte | Beschreibung |
|-----------|--------|--------------|
| Klassenübereinstimmung | +100 | Lehrkraft unterrichtet die Klasse |
| Fahrzeit ≤5 min Umweg | +50 | Exzellente Lage |
| Fahrzeit 5-10 min Umweg | +30 | Gute Lage |
| Fahrzeit 10-20 min Umweg | +10 | Akzeptable Lage |
| Einrichtung bereits betreut | +30 | Konsistenz-Bonus |
| Abweichung von Soll-Anzahl | -20 pro Abweichung | Lastverteilung |

## Konfiguration anpassen

In `config.json` können Sie folgende Parameter ändern:

```json
{
  "scoring": {
    "klassen_match": 100,           // Punkte für Klassenübereinstimmung
    "fahrzeit_exzellent": 50,       // Punkte für ≤5 min Umweg
    "fahrzeit_gut": 30,             // Punkte für ≤10 min Umweg
    "fahrzeit_akzeptabel": 10,      // Punkte für ≤20 min Umweg
    "einrichtung_konsistenz": 30,   // Punkte für gleiche Einrichtung
    "abweichung_soll_malus": 20     // Malus pro Abweichung von Soll-Anzahl
  },
  "fahrzeit_grenzen": {
    "exzellent_max_min": 5,         // Grenze für "exzellent"
    "gut_max_min": 10,              // Grenze für "gut"
    "akzeptabel_max_min": 20        // Grenze für "akzeptabel"
  }
}
```

## Beispiel-Dateien

Zum Testen des Tools:

```bash
python beispiel_schuelerinnen.py
```

Dies erstellt:
- `beispiel_schuelerinnen.xlsx`
- `beispiel_lehrkraefte.xlsx`

## Technische Details

- **Geocodierung**: Nominatim (OpenStreetMap)
- **Routing**: OpenRouteService (driving-car profile)
- **Caching**: Adressen und Routen werden gecached
- **Rate Limiting**: Automatische Verzögerungen für API-Anfragen
- **Fallback**: Bei API-Fehlern wird auf Luftlinien-Schätzung zurückgegriffen

## Fehlerbehebung

### "API-Key nicht eingetragen"
→ Tragen Sie Ihren OpenRouteService API-Key in `config.json` ein

### "Adresse nicht gefunden"
→ Prüfen Sie die Adressformate in der Excel-Datei

### "API-Limit erreicht"
→ Warten Sie bis zum nächsten Tag (2000 Anfragen/Tag kostenlos)

### "Fehlende Spalten"
→ Überprüfen Sie die Spaltennamen in den Excel-Dateien

## Lizenz

Dieses Tool wurde für die Praktikumsverwaltung an Fachschulen entwickelt.
