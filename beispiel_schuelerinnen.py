#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erstellt Beispiel-Excel-Dateien für Tests
"""
import pandas as pd

# Beispiel Schülerinnen
schueler_data = {
    'Name': [
        'Anna Schmidt', 'Lisa Müller', 'Sarah Weber', 'Julia Koch',
        'Marie Becker', 'Laura Wagner', 'Sophie Schulz', 'Emma Fischer',
        'Lena Meyer', 'Hannah Hoffmann'
    ],
    'Klasse': [
        'FSP23a', 'FSP23a', 'FSP23b', 'FSP23b',
        'FSP24a', 'FSP24a', 'FSP23a', 'FSP23b',
        'FSP24a', 'FSP23b'
    ],
    'Einrichtung': [
        'Kita Sonnenschein', 'Kita Regenbogen', 'Kita Sonnenschein', 'Kindergarten Waldweg',
        'Kita Abenteuerland', 'Kita Regenbogen', 'Kindergarten Waldweg', 'Kita Sterntaler',
        'Kita Abenteuerland', 'Kita Sterntaler'
    ],
    'Straße': [
        'Hauptstraße 12', 'Bahnhofstraße 5', 'Hauptstraße 12', 'Waldstraße 23',
        'Schulweg 8', 'Bahnhofstraße 5', 'Waldstraße 23', 'Marktplatz 3',
        'Schulweg 8', 'Marktplatz 3'
    ],
    'PLZ': [
        '24768', '24768', '24768', '24782',
        '24787', '24768', '24782', '24768',
        '24787', '24768'
    ],
    'Ort': [
        'Rendsburg', 'Rendsburg', 'Rendsburg', 'Büdelsdorf',
        'Fockbek', 'Rendsburg', 'Büdelsdorf', 'Rendsburg',
        'Fockbek', 'Rendsburg'
    ]
}

# Beispiel Lehrkräfte
lehrkraefte_data = {
    'Name': [
        'Frau Meyer', 'Herr Schmidt', 'Frau Fischer', 'Frau Wagner', 'Herr Hoffmann'
    ],
    'PLZ_Wohnort': [
        '24768',  # Rendsburg
        '24782',  # Büdelsdorf
        '24787',  # Fockbek
        '24768',  # Rendsburg
        '24796'   # Bredenbek
    ],
    'Klassen': [
        'FSP23a, FSP23b',
        'FSP23b, FSP24a',
        'FSP24a',
        'FSP23a',
        'FSP23b, FSP24a'
    ],
    'Soll_Anzahl_Betreuungen': [
        3, 2, 2, 2, 1
    ]
}

# Excel-Dateien erstellen
schueler_df = pd.DataFrame(schueler_data)
lehrkraefte_df = pd.DataFrame(lehrkraefte_data)

schueler_df.to_excel('beispiel_schuelerinnen.xlsx', index=False)
lehrkraefte_df.to_excel('beispiel_lehrkraefte.xlsx', index=False)

print("✓ Beispiel-Dateien erstellt:")
print("  - beispiel_schuelerinnen.xlsx")
print("  - beispiel_lehrkraefte.xlsx")
