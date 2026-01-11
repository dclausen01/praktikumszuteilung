import pandas as pd

# Lehrkräfte
lk = pd.read_excel('beispiel_lehrkraefte.xlsx')
print("=== LEHRKRÄFTE ===")
print(lk.to_string())
print()

# Schülerinnen
sus = pd.read_excel('beispiel_schuelerinnen.xlsx')
print(f"=== SCHÜLERINNEN (Total: {len(sus)}) ===")
print(f"Klassen: {list(sus['Klasse'].unique())}")
print()
print("Klassen-Verteilung:")
print(sus['Klasse'].value_counts())
print()

# Prüfe BedbA
bedba = lk[lk['Name'] == 'BedbA']
if not bedba.empty:
    print("=== BedbA Details ===")
    print(f"PLZ: {bedba.iloc[0]['PLZ_Wohnort']}")
    print(f"Klassen: {bedba.iloc[0]['Klassen']}")
    print(f"Soll: {bedba.iloc[0]['Soll_Anzahl_Betreuungen']}")

    bedba_klassen = [k.strip() for k in str(bedba.iloc[0]['Klassen']).split(',')]
    print(f"Parsed Klassen: {bedba_klassen}")

    # Zähle Schülerinnen in BedbAs Klassen
    sus_in_bedba_klassen = sus[sus['Klasse'].isin(bedba_klassen)]
    print(f"Schülerinnen in BedbAs Klassen: {len(sus_in_bedba_klassen)}")
    if len(sus_in_bedba_klassen) > 0:
        print("Klassen-Breakdown:")
        print(sus_in_bedba_klassen['Klasse'].value_counts())

# Zuteilung
print("\n=== ZUTEILUNG ===")
zut = pd.read_excel('Zuteilung_2026_FSP25a_FSP25c_FSP25d.xlsx', sheet_name='Zuteilungen')
print(f"Total Zuweisungen: {len(zut)}")
print("\nZuweisungen pro Lehrkraft:")
print(zut['Lehrkraft'].value_counts())
