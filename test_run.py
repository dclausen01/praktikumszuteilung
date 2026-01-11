#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatischer Testlauf des Praktikumszuteilungs-Tools
"""
import sys
from praktikumszuteilung import PraktikumszuteilungTool

def main():
    print("=" * 60)
    print("  PRAKTIKUMSZUTEILUNGS-TOOL - TESTLAUF")
    print("=" * 60)

    # Tool initialisieren
    try:
        tool = PraktikumszuteilungTool()
    except Exception as e:
        print(f"❌ Fehler beim Laden der Konfiguration: {e}")
        return

    # Beispieldateien verwenden
    schueler_path = "beispiel_schuelerinnen.xlsx"
    lehrkraefte_path = "beispiel_lehrkraefte.xlsx"

    print(f"\n📋 Verwende Testdateien:")
    print(f"   Schülerinnen: {schueler_path}")
    print(f"   Lehrkräfte: {lehrkraefte_path}")

    # Daten laden
    try:
        schueler_df, lehrkraefte_df = tool.load_data(schueler_path, lehrkraefte_path)
    except Exception as e:
        print(f"❌ Fehler beim Laden der Daten: {e}")
        import traceback
        traceback.print_exc()
        return

    # Zuteilung durchführen
    try:
        results_df = tool.assign_praktika(schueler_df, lehrkraefte_df)
        output_file = tool.save_results(results_df, schueler_df)

        print("\n" + "=" * 60)
        print("✅ TESTLAUF ERFOLGREICH ABGESCHLOSSEN!")
        print(f"   Ausgabedatei: {output_file}")
        print("=" * 60)

        # Zeige Zusammenfassung
        print("\n📊 ZUSAMMENFASSUNG:")
        print(f"   Insgesamt {len(results_df)} Schülerinnen zugeteilt")
        print("\n   Verteilung pro Lehrkraft:")
        for lehrkraft in results_df.groupby('Lehrkraft'):
            name = lehrkraft[0]
            count = len(lehrkraft[1])
            einrichtungen = lehrkraft[1]['Einrichtung'].nunique()
            avg_score = lehrkraft[1]['Score'].mean()
            print(f"   - {name}: {count} Schüler, {einrichtungen} Einrichtung(en), Ø Score: {avg_score:.1f}")

    except Exception as e:
        print(f"\n❌ Fehler bei der Zuteilung: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
