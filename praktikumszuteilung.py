#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Praktikumszuteilungs-Tool
Automatische Zuteilung von Lehrkräften zu Schülerinnen-Praktika
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import pandas as pd
import openrouteservice
from openrouteservice import client
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import time


class PraktikumszuteilungTool:
    def __init__(self, config_path: str = "config.json"):
        """Initialisiert das Tool mit Konfiguration"""
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        self.api_key = self.config['api_key']
        if self.api_key == "HIER_IHREN_OPENROUTESERVICE_API_KEY_EINTRAGEN":
            print("⚠️  WARNUNG: Bitte tragen Sie Ihren OpenRouteService API-Key in config.json ein!")
            print("   Registrierung: https://openrouteservice.org/dev/#/signup")
            sys.exit(1)

        # ORS Client mit deaktiviertem Retry (wir behandeln Rate-Limits selbst)
        self.ors_client = client.Client(key=self.api_key, retry_over_query_limit=False)
        self.geolocator = Nominatim(user_agent="praktikumszuteilung_tool")
        self.geocode_cache = {}
        self.route_cache = {}

        # Schule geocodieren
        self.schule_adresse = self.config['schule_adresse']
        self.schule_coords = self._geocode(self.schule_adresse)
        print(f"✓ Schule geocodiert: {self.schule_coords}")

    def _geocode(self, adresse: str, plz: str = None) -> Tuple[float, float]:
        """
        Geocodiert eine Adresse zu Koordinaten (Lat, Lon)
        Mit Fallback auf PLZ-basierte Suche bei Fehlern
        """
        if adresse in self.geocode_cache:
            return self.geocode_cache[adresse]

        try:
            time.sleep(1)  # Nominatim rate limit
            location = self.geolocator.geocode(adresse)
            if location:
                coords = (location.latitude, location.longitude)
                self.geocode_cache[adresse] = coords
                return coords
            else:
                # Fallback: Versuche nur mit PLZ
                if plz:
                    print(f"⚠️  Adresse nicht gefunden: {adresse}")
                    print(f"   → Fallback: Versuche nur PLZ {plz}")
                    time.sleep(1)
                    plz_location = self.geolocator.geocode(f"{plz}, Deutschland")
                    if plz_location:
                        coords = (plz_location.latitude, plz_location.longitude)
                        self.geocode_cache[adresse] = coords
                        print(f"   ✓ PLZ-basierte Geocodierung erfolgreich")
                        return coords
                print(f"⚠️  Adresse und PLZ nicht gefunden: {adresse}")
                return None
        except Exception as e:
            print(f"⚠️  Geocoding-Fehler für {adresse}: {e}")
            # Auch bei Ausnahme: Fallback auf PLZ
            if plz:
                try:
                    print(f"   → Fallback: Versuche nur PLZ {plz}")
                    time.sleep(1)
                    plz_location = self.geolocator.geocode(f"{plz}, Deutschland")
                    if plz_location:
                        coords = (plz_location.latitude, plz_location.longitude)
                        self.geocode_cache[adresse] = coords
                        print(f"   ✓ PLZ-basierte Geocodierung erfolgreich")
                        return coords
                except Exception as plz_error:
                    print(f"   ⚠️  Auch PLZ-Geocoding fehlgeschlagen: {plz_error}")
            return None

    def _get_route_duration(self, start_coords: Tuple[float, float],
                           end_coords: Tuple[float, float], retry_on_rate_limit: bool = True) -> Optional[float]:
        """
        Berechnet Fahrtzeit in Minuten zwischen zwei Koordinaten
        Mit Fallback auf Luftlinien-Schätzung bei Routing-Fehlern
        """
        cache_key = f"{start_coords}_{end_coords}"
        if cache_key in self.route_cache:
            return self.route_cache[cache_key]

        try:
            # OpenRouteService erwartet (lon, lat) statt (lat, lon)
            coords = [[start_coords[1], start_coords[0]],
                     [end_coords[1], end_coords[0]]]

            route = self.ors_client.directions(
                coordinates=coords,
                profile='driving-car',
                format='geojson'
            )

            # Dauer in Sekunden, umrechnen in Minuten
            duration_min = route['features'][0]['properties']['segments'][0]['duration'] / 60
            self.route_cache[cache_key] = duration_min
            time.sleep(1.6)  # Rate limiting: 40 req/min → 1.5s + Puffer
            return duration_min

        except openrouteservice.exceptions.ApiError as e:
            error_str = str(e)

            # Behandlung von Rate-Limit (HTTP 429)
            if '429' in error_str or 'rate limit' in error_str.lower():
                if retry_on_rate_limit:
                    print(f"⚠️  Rate-Limit erreicht! Warte 65 Sekunden...")
                    time.sleep(65)
                    print(f"   → Setze Verarbeitung fort...")
                    # Rekursiver Aufruf ohne weiteres Retry
                    return self._get_route_duration(start_coords, end_coords, retry_on_rate_limit=False)
                else:
                    print(f"⚠️  Rate-Limit bleibt, nutze Luftlinien-Schätzung")

            # Stille Behandlung von bekannten Routing-Problemen
            elif '404' in error_str and '2010' in error_str:
                # Koordinate nicht routingfähig (z.B. auf Wiese/im Wasser) → stiller Fallback
                pass
            elif '2099' in error_str:
                # Keine Route gefunden → stiller Fallback
                pass
            else:
                # Nur bei unerwarteten Fehlern ausgeben
                print(f"⚠️  Routing-Fehler: {e}")

            # Fallback auf Luftlinie
            dist_km = geodesic(start_coords, end_coords).kilometers
            duration_min = dist_km * 1.5  # Schätzung: 1km ≈ 1.5min
            self.route_cache[cache_key] = duration_min
            return duration_min

        except Exception as e:
            # Nur unerwartete Fehler ausgeben
            if 'rate limit' not in str(e).lower():
                print(f"⚠️  Unerwarteter Routing-Fehler: {e}")

            # Fallback auf Luftlinie
            dist_km = geodesic(start_coords, end_coords).kilometers
            duration_min = dist_km * 1.5  # Schätzung: 1km ≈ 1.5min
            self.route_cache[cache_key] = duration_min
            return duration_min

    def _calculate_detour(self, lehrkraft_coords: Tuple[float, float],
                         einrichtung_coords: Tuple[float, float]) -> float:
        """
        Bewertet die Erreichbarkeit der Einrichtung basierend auf GESAMT-Fahrtzeit (Hin + Rück):
        - Option 1: Von Schule hin und zurück (Schule → Einrichtung → Schule)
        - Option 2: Von Wohnort hin und zurück (Wohnort → Einrichtung → Wohnort)
        - Option 3: Kompletter Weg Wohnort → Einrichtung → Schule → Wohnort

        Nimmt die günstigste Option als Bewertung.
        WICHTIG: Alle Zeiten sind Gesamt-Fahrzeiten (round-trip), nicht nur Hinweg!
        """
        if not lehrkraft_coords or not einrichtung_coords:
            return 999  # Ungültige Koordinaten

        # Berechne relevante Fahrzeiten (einzelne Strecken)
        schule_to_einrichtung = self._get_route_duration(self.schule_coords, einrichtung_coords)
        wohnort_to_einrichtung = self._get_route_duration(lehrkraft_coords, einrichtung_coords)
        wohnort_to_schule = self._get_route_duration(lehrkraft_coords, self.schule_coords)
        einrichtung_to_schule = self._get_route_duration(einrichtung_coords, self.schule_coords)

        # Option 1: Von Schule aus (hin + zurück)
        # Schule → Einrichtung → Schule
        from_school_roundtrip = schule_to_einrichtung * 2

        # Option 2: Von Wohnort aus (hin + zurück)
        # Wohnort → Einrichtung → Wohnort
        from_home_roundtrip = wohnort_to_einrichtung * 2

        # Option 3: Kompletter Weg mit Einrichtung
        # Wohnort → Einrichtung → Schule → Wohnort
        # Dies ist relevant, wenn Lehrkraft auf dem Weg zur/von Schule die Einrichtung besuchen kann
        complete_trip_via_einrichtung = wohnort_to_einrichtung + einrichtung_to_schule + wohnort_to_schule

        # Vergleich mit direktem Weg Wohnort → Schule → Wohnort
        normal_commute = wohnort_to_schule * 2

        # Der "Umweg" ist die Differenz zum normalen Weg
        # Wenn negativ, ist der Weg über Einrichtung sogar kürzer (liegt perfekt auf dem Weg)
        detour_time = complete_trip_via_einrichtung - normal_commute

        # Nimm das Minimum aller Optionen als "effektive Gesamt-Fahrtzeit"
        # Detour-Zeit kann negativ sein, wenn Einrichtung perfekt auf dem Weg liegt - dann ist es effektiv 0
        effective_time = min(from_school_roundtrip, from_home_roundtrip, max(0, detour_time))

        return effective_time

    def _is_within_capacity(self, lehrkraft: pd.Series, current_assignments: Dict[str, List[str]]) -> bool:
        """
        Prüft, ob Lehrkraft noch Kapazität hat (harte Grenze: Soll +1)
        """
        current_count = len(current_assignments.get(lehrkraft['Name'], []))
        soll_anzahl = lehrkraft['Soll_Anzahl_Betreuungen']
        return current_count < soll_anzahl + 1

    def _calculate_score(self, lehrkraft: pd.Series, schueler: pd.Series,
                        einrichtung_coords: Tuple[float, float],
                        current_assignments: Dict[str, List[str]]) -> Tuple[float, str]:
        """
        Berechnet Score für Lehrkraft-Schüler-Paarung
        Returns: (score, begründung)
        """
        score = 0
        reasons = []

        # Kriterium 3 (Prio 1): Klassenübereinstimmung
        lehrkraft_klassen = [k.strip() for k in str(lehrkraft['Klassen']).split(',')]
        if schueler['Klasse'] in lehrkraft_klassen:
            score += self.config['scoring']['klassen_match']
            reasons.append(f"Unterrichtet in {schueler['Klasse']}")

        # Kriterium 2 (Prio 2): Fahrzeit/Erreichbarkeit
        lehrkraft_plz = str(lehrkraft['PLZ_Wohnort'])
        lehrkraft_adresse = f"{lehrkraft_plz}, Deutschland"
        lehrkraft_coords = self._geocode(lehrkraft_adresse)

        if lehrkraft_coords and einrichtung_coords:
            # _calculate_detour gibt jetzt die beste Gesamt-Fahrzeit zurück (round-trip!)
            effective_travel_time = self._calculate_detour(lehrkraft_coords, einrichtung_coords)

            # Bonus für kurze Fahrzeiten
            if effective_travel_time <= self.config['fahrzeit_grenzen']['exzellent_max_min']:
                score += self.config['scoring']['fahrzeit_exzellent']
                reasons.append(f"Fahrzeit: {effective_travel_time:.1f} min (exzellent)")
            elif effective_travel_time <= self.config['fahrzeit_grenzen']['gut_max_min']:
                score += self.config['scoring']['fahrzeit_gut']
                reasons.append(f"Fahrzeit: {effective_travel_time:.1f} min (gut)")
            elif effective_travel_time <= self.config['fahrzeit_grenzen']['akzeptabel_max_min']:
                score += self.config['scoring']['fahrzeit_akzeptabel']
                reasons.append(f"Fahrzeit: {effective_travel_time:.1f} min (akzeptabel)")
            else:
                reasons.append(f"Fahrzeit: {effective_travel_time:.1f} min (ungünstig)")

            # Malus für sehr lange Fahrzeiten
            if effective_travel_time > self.config['fahrzeit_grenzen']['sehr_lang_min']:
                malus = self.config['scoring']['fahrzeit_sehr_lang_malus']
                score -= malus
                reasons.append(f"Sehr lange Fahrt >{self.config['fahrzeit_grenzen']['sehr_lang_min']}min (-{malus})")
            elif effective_travel_time > self.config['fahrzeit_grenzen']['lang_min']:
                malus = self.config['scoring']['fahrzeit_lang_malus']
                score -= malus
                reasons.append(f"Lange Fahrt >{self.config['fahrzeit_grenzen']['lang_min']}min (-{malus})")

            # Rendsburg-Bonus: Lehrkräfte aus Rendsburg-Umgebung erhalten Bonus für Rendsburg-Einrichtungen
            einrichtung_plz = str(schueler['PLZ'])
            if (lehrkraft_plz.startswith(self.config['rendsburg_plz_praefix']) and
                einrichtung_plz.startswith(self.config['rendsburg_plz_praefix'])):
                bonus = self.config['scoring']['rendsburg_bonus']
                score += bonus
                reasons.append(f"Rendsburg-Region (+{bonus})")

        # Kriterium 1 (Prio 3): Einrichtungskonsistenz
        einrichtung = schueler['Einrichtung']
        if lehrkraft['Name'] in current_assignments:
            assigned_einrichtungen = set([e for _, e in current_assignments[lehrkraft['Name']]])
            if einrichtung in assigned_einrichtungen:
                score += self.config['scoring']['einrichtung_konsistenz']
                reasons.append("Betreut bereits diese Einrichtung")

        # Lastverteilung - nur Abweichungen außerhalb von Soll ±1 bestrafen
        current_count = len(current_assignments.get(lehrkraft['Name'], []))
        soll_anzahl = lehrkraft['Soll_Anzahl_Betreuungen']

        # Bonus für Lehrkräfte, die unter Soll sind (je weiter unter Soll, desto höher der Bonus)
        if current_count < soll_anzahl:
            # Positiver Bonus für Lehrkräfte unter Soll (ausgeglichene Verteilung fördern)
            bonus = (soll_anzahl - current_count) * 5
            score += bonus
            reasons.append(f"Ist/Soll: {current_count}/{soll_anzahl} (+{bonus})")
        elif current_count == soll_anzahl:
            # Exakt am Soll: leichter Malus, damit andere bevorzugt werden
            score -= 10
            reasons.append(f"Ist/Soll: {current_count}/{soll_anzahl} (-10)")
        else:
            # Über Soll: Malus
            abweichung = current_count - soll_anzahl
            malus = abweichung * self.config['scoring']['abweichung_soll_malus']
            score -= malus
            reasons.append(f"Ist/Soll: {current_count}/{soll_anzahl} (-{malus})")

        return score, " | ".join(reasons)

    def load_data(self, schueler_path: str, lehrkraefte_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Lädt Excel-Dateien"""
        print("\n📂 Lade Daten...")
        schueler_df = pd.read_excel(schueler_path)
        lehrkraefte_df = pd.read_excel(lehrkraefte_path)

        print(f"   ✓ {len(schueler_df)} Schülerinnen geladen")
        print(f"   ✓ {len(lehrkraefte_df)} Lehrkräfte geladen")

        return schueler_df, lehrkraefte_df

    def assign_praktika(self, schueler_df: pd.DataFrame,
                       lehrkraefte_df: pd.DataFrame) -> pd.DataFrame:
        """
        Führt optimale Zuteilung durch mit harten Kapazitätsgrenzen.
        Strategie: Berechne alle Scores, sortiere nach Score, weise beste Matches zuerst zu.
        """
        print("\n🔄 Starte Zuteilung...")

        # Prüfe, ob genug Kapazität vorhanden ist
        total_capacity = lehrkraefte_df['Soll_Anzahl_Betreuungen'].sum() + len(lehrkraefte_df)  # +1 pro Lehrkraft
        total_students = len(schueler_df)
        if total_capacity < total_students:
            print(f"⚠️  WARNUNG: Nicht genug Kapazität!")
            print(f"   Schülerinnen: {total_students}, Max. Kapazität: {total_capacity}")
            print(f"   Einige Zuweisungen können fehlschlagen.")

        # Geocodiere alle Einrichtungen
        print("\n📍 Geocodiere Einrichtungen...")
        schueler_df['Adresse_voll'] = schueler_df.apply(
            lambda x: f"{x['Straße']}, {x['PLZ']} {x['Ort']}", axis=1
        )
        schueler_df['PLZ_str'] = schueler_df['PLZ'].astype(str)
        schueler_df['Coords'] = schueler_df.apply(
            lambda x: self._geocode(x['Adresse_voll'], x['PLZ_str']), axis=1
        )

        # Phase 1: Berechne ALLE möglichen Paarungen mit initialen Scores
        print("\n🎯 Berechne alle möglichen Zuordnungen...")
        all_matches = []  # Liste von (score, schueler_idx, lehrkraft_idx, reason)

        # Dummy current_assignments für initiale Score-Berechnung
        # Wir berechnen Scores ohne Einrichtungskonsistenz-Bonus, da noch niemand zugeteilt ist
        empty_assignments = {}

        for s_idx, schueler in schueler_df.iterrows():
            for l_idx, lehrkraft in lehrkraefte_df.iterrows():
                score, reason = self._calculate_score(
                    lehrkraft, schueler, schueler['Coords'], empty_assignments
                )
                all_matches.append({
                    'score': score,
                    'schueler_idx': s_idx,
                    'lehrkraft_idx': l_idx,
                    'schueler_name': schueler['Name'],
                    'lehrkraft_name': lehrkraft['Name'],
                    'einrichtung': schueler['Einrichtung'],
                    'reason': reason
                })

        # Sortiere alle Matches nach Score (höchster zuerst)
        all_matches.sort(key=lambda x: x['score'], reverse=True)
        print(f"   ✓ {len(all_matches)} mögliche Paarungen berechnet")

        # Phase 2: Iterative Zuteilung mit Score-Updates
        print("\n📋 Weise beste Matches zu (mit dynamischen Score-Updates)...")
        assignments = []
        current_assignments = {}  # Lehrkraft → [(Schüler, Einrichtung)]
        assigned_students = set()  # Set der bereits zugewiesenen Schüler-Indizes

        iteration = 0
        max_iterations = len(schueler_df) * 10  # Sicherheit gegen Endlosschleife

        while len(assigned_students) < len(schueler_df) and iteration < max_iterations:
            iteration += 1

            # Neuberechnung aller Scores mit aktuellen Zuweisungen
            available_matches = []
            for s_idx, schueler in schueler_df.iterrows():
                if s_idx in assigned_students:
                    continue

                for l_idx, lehrkraft in lehrkraefte_df.iterrows():
                    # Prüfe Kapazität
                    if not self._is_within_capacity(lehrkraft, current_assignments):
                        continue

                    # Berechne aktuellen Score (mit Einrichtungskonsistenz-Bonus!)
                    score, reason = self._calculate_score(
                        lehrkraft, schueler, schueler['Coords'], current_assignments
                    )

                    available_matches.append({
                        'score': score,
                        'schueler_idx': s_idx,
                        'schueler_name': schueler['Name'],
                        'klasse': schueler['Klasse'],
                        'einrichtung': schueler['Einrichtung'],
                        'adresse': schueler['Adresse_voll'],
                        'lehrkraft_name': lehrkraft['Name'],
                        'lehrkraft_soll': lehrkraft['Soll_Anzahl_Betreuungen'],
                        'reason': reason
                    })

            if not available_matches:
                # Keine verfügbaren Matches mehr
                break

            # Wähle bestes verfügbares Match
            available_matches.sort(key=lambda x: x['score'], reverse=True)
            best_match = available_matches[0]

            # Zuteilung durchführen
            assignments.append({
                'Schülerin': best_match['schueler_name'],
                'Klasse': best_match['klasse'],
                'Einrichtung': best_match['einrichtung'],
                'Adresse': best_match['adresse'],
                'Lehrkraft': best_match['lehrkraft_name'],
                'Score': best_match['score'],
                'Begründung': best_match['reason']
            })

            # Update current assignments
            if best_match['lehrkraft_name'] not in current_assignments:
                current_assignments[best_match['lehrkraft_name']] = []
            current_assignments[best_match['lehrkraft_name']].append(
                (best_match['schueler_name'], best_match['einrichtung'])
            )

            assigned_students.add(best_match['schueler_idx'])

            current_count = len(current_assignments[best_match['lehrkraft_name']])
            soll = best_match['lehrkraft_soll']
            print(f"   ✓ {best_match['schueler_name']} → {best_match['lehrkraft_name']} "
                  f"(Score: {best_match['score']:.1f}, {current_count}/{soll})")

        # Prüfe auf nicht zugewiesene Schülerinnen
        if len(assigned_students) < len(schueler_df):
            print(f"\n⚠️  WARNUNG: {len(schueler_df) - len(assigned_students)} Schülerinnen konnten nicht zugeteilt werden!")
            for s_idx, schueler in schueler_df.iterrows():
                if s_idx not in assigned_students:
                    print(f"   ❌ Nicht zugeteilt: {schueler['Name']}")

        # Abschließende Validierung
        print("\n📊 Validiere Kapazitätsgrenzen...")
        for _, lehrkraft in lehrkraefte_df.iterrows():
            count = len(current_assignments.get(lehrkraft['Name'], []))
            soll = lehrkraft['Soll_Anzahl_Betreuungen']
            if count < soll - 1:
                print(f"   ⚠️  {lehrkraft['Name']}: {count}/{soll} (Unterlast: {soll - count})")
            elif count > soll + 1:
                print(f"   ❌ {lehrkraft['Name']}: {count}/{soll} (ÜBERLAST: {count - soll})!")
            elif count != soll:
                print(f"   ✓ {lehrkraft['Name']}: {count}/{soll} (Abweichung: {count - soll})")
            else:
                print(f"   ✓ {lehrkraft['Name']}: {count}/{soll} (exakt)")

        return pd.DataFrame(assignments)

    def save_results(self, results_df: pd.DataFrame, schueler_df: pd.DataFrame):
        """Speichert Ergebnisse als Excel"""
        # Ermittle beteiligte Klassen
        klassen = sorted(schueler_df['Klasse'].unique())
        klassen_str = "_".join(klassen)
        jahr = datetime.now().year

        output_filename = f"Zuteilung_{jahr}_{klassen_str}.xlsx"

        print(f"\n💾 Speichere Ergebnisse: {output_filename}")

        # Erstelle Excel mit formatiertem Output
        with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
            results_df.to_excel(writer, sheet_name='Zuteilungen', index=False)

            # Statistik-Sheet
            stats = results_df.groupby('Lehrkraft').agg({
                'Schülerin': 'count',
                'Einrichtung': lambda x: x.nunique()
            }).rename(columns={'Schülerin': 'Anzahl_Schüler', 'Einrichtung': 'Anzahl_Einrichtungen'})
            stats.to_excel(writer, sheet_name='Statistik')

        print(f"   ✓ Datei gespeichert: {output_filename}")
        return output_filename


def main():
    """Interaktive Hauptfunktion"""
    print("=" * 60)
    print("  PRAKTIKUMSZUTEILUNGS-TOOL")
    print("  Automatische Zuteilung von Lehrkräften zu Praktika")
    print("=" * 60)

    # Config laden
    try:
        tool = PraktikumszuteilungTool()
    except Exception as e:
        print(f"❌ Fehler beim Laden der Konfiguration: {e}")
        return

    # Dateiauswahl
    print("\n📋 Bitte geben Sie die Dateipfade ein:")
    schueler_path = input("   Schülerinnen-Datei (Excel): ").strip().strip('"')
    lehrkraefte_path = input("   Lehrkräfte-Datei (Excel): ").strip().strip('"')

    if not os.path.exists(schueler_path):
        print(f"❌ Datei nicht gefunden: {schueler_path}")
        return
    if not os.path.exists(lehrkraefte_path):
        print(f"❌ Datei nicht gefunden: {lehrkraefte_path}")
        return

    # Daten laden
    try:
        schueler_df, lehrkraefte_df = tool.load_data(schueler_path, lehrkraefte_path)
    except Exception as e:
        print(f"❌ Fehler beim Laden der Daten: {e}")
        return

    # Validierung
    erforderliche_spalten_schueler = ['Name', 'Klasse', 'Einrichtung', 'Straße', 'PLZ', 'Ort']
    erforderliche_spalten_lehrkraefte = ['Name', 'PLZ_Wohnort', 'Klassen', 'Soll_Anzahl_Betreuungen']

    fehlende_schueler = [s for s in erforderliche_spalten_schueler if s not in schueler_df.columns]
    fehlende_lehrkraefte = [s for s in erforderliche_spalten_lehrkraefte if s not in lehrkraefte_df.columns]

    if fehlende_schueler:
        print(f"❌ Fehlende Spalten in Schülerinnen-Datei: {fehlende_schueler}")
        return
    if fehlende_lehrkraefte:
        print(f"❌ Fehlende Spalten in Lehrkräfte-Datei: {fehlende_lehrkraefte}")
        return

    # Zuteilung durchführen
    try:
        results_df = tool.assign_praktika(schueler_df, lehrkraefte_df)
        output_file = tool.save_results(results_df, schueler_df)

        print("\n" + "=" * 60)
        print("✅ ZUTEILUNG ERFOLGREICH ABGESCHLOSSEN!")
        print(f"   Ausgabedatei: {output_file}")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Fehler bei der Zuteilung: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
