# DACH Firmenkredit-, Annuitäten- & Tilgungsplan-Rechner 2026 🏢

[![CI Matrix](https://github.com/DACHDigitalwerk/kredit-annuitaeten-rechner-dach/actions/workflows/ci.yml/badge.svg)](https://github.com/DACHDigitalwerk/kredit-annuitaeten-rechner-dach/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Platform: Web App](https://img.shields.io/badge/Live%20App-DACH%20Digitalwerk-emerald.svg)](https://dachdigitalwerk.github.io/kredit-annuitaeten-rechner/)

Rechtskonformer und performanter Python- und CLI-Präzisionsrechner für **Firmenkredite, Annuitätendarlehen, PAngV Effektivzins**, jährliche **Sondertilgungen**, **Zinsbindungsfristen**, **Restschuldermittlung** und **Zins-Stresstests** für die Anschlussfinanzierung im DACH-Raum (Deutschland, Österreich und Schweiz).

---

## 🌟 Kernfunktionen

1. **Darlehensformen:**
   - **Annuitätendarlehen:** Konstante Ratenzahlung, kontinuierlich sinkender Zinsanteil und ansteigender Tilgungsanteil.
   - **Tilgungsdarlehen:** Feste periodische Tilgung, degressive Gesamtbelastung durch sinkende Zinsen.
   - **Endfälliges Darlehen:** Laufende Zahlung reiner Zinsen, vollständige Tilgung bei Fälligkeit.
2. **PAngV Effektivzins-Berechnung:**
   - Exakte Ermittlung des effektiven Jahreszinses nach der deutschen Preisangabenverordnung (PAngV) unter Berücksichtigung unterjähriger Zahlungsintervalle (monatlich / quartalsweise) und Auszahlungskursen (Disagio).
3. **Flexible Sondertilgungen:**
   - Modellierung jährlicher Sondertilgungen (z. B. 5 % der Darlehenssumme) mit automatischer Verkürzung der Gesamtlaufzeit und Einsparung von Zinskosten.
4. **Zinsänderungs-Stresstest für die Anschlussfinanzierung:**
   - Automatische Simulation von Zinssprüngen um **+1 %, +2 %, +3 % und +4 %** nach Ende der Zinsbindung.
   - Ermittlung der monatlichen Mehrbelastung und der zusätzlichen Zinskosten über 5 Jahre.
5. **DACH-Ländermodi:**
   - **Deutschland:** PAngV Effektivzins & § 489 Abs. 1 Nr. 2 BGB Sonderkündigungsrecht nach 10 Jahren ohne Vorfälligkeitsentschädigung.
   - **Österreich:** Kreditvertragsgebühr gem. GebG § 33 TP 8 (0,8 % Rechtsgeschäftsgebühr für gewerbliche Kredite; Befreiung für privaten Wohnbau) und Euribor-Bindung.
   - **Schweiz:** Hypotheken-Tragbarkeitsprüfung mit 5,0 % kalkulatorischem Zinssatz, 1,0 % Unterhaltskosten und Amortisation der 2. Hypothek in 15 Jahren (Maximalbelastung: 33,3 % des Bruttoeinkommens).

---

## 🚀 Installation

```bash
pip install .
```

Oder im Entwicklermodus:
```bash
git clone https://github.com/DACHDigitalwerk/kredit-annuitaeten-rechner-dach.git
cd kredit-annuitaeten-rechner-dach
pip install -e ".[dev]"
```

---

## 💻 CLI-Nutzung (`dach-kredit`)

### 1. Standard-Annuitätendarlehen berechnen
```bash
dach-kredit --amount 250000 --interest 3.8 --repayment 2.5 --fixed-years 10
```

### 2. Mit jährlicher Sondertilgung und JSON-Ausgabe
```bash
dach-kredit --amount 300000 --interest 3.5 --repayment 2.0 --special-repayment 5000 --json
```

### 3. Österreichischer Gewerbekredit (GebG Gebühr)
```bash
dach-kredit --amount 500000 --country AT
```

### 4. Schweizer Hypotheken-Tragbarkeit
```bash
dach-kredit --country CH --amount 800000 --property-value 1200000 --gross-income 190000
```

---

## 🐍 Python-API

```python
from kredit_dach import calculate_loan, LoanType, PaymentInterval

loan = calculate_loan(
    loan_amount=250000.0,
    nominal_interest_rate=0.038, # 3,8 %
    initial_repayment_rate=0.025, # 2,5 %
    loan_type=LoanType.ANNUITY,
    interval=PaymentInterval.MONTHLY,
    fixed_interest_years=10,
    annual_special_repayment=5000.0
)

print(f"Monatliche Rate: {loan.regular_installment:.2f} €")
print(f"Restschuld nach 10 Jahren: {loan.remaining_balance_fixed_term:.2f} €")
print(f"Volltilgung nach: {loan.full_amortization_years:.1f} Jahren")
```

---

## 🧪 Tests

```bash
pytest tests/ -v
```

---

## ⚖️ Lizenz & Haftungsausschluss

Veröffentlicht unter der [MIT License](LICENSE).

**Rechtlicher Hinweis (BGH Smartlaw Az. I ZR 113/20 & I ZR 226/20):**
Dieses Tool stellt ein unverbindliches mathematisches Berechnungswerkzeug dar und ersetzt keine individuelle Kredit- oder Finanzierungsberatung durch ein Kreditinstitut oder einen zertifizierten Finanzierungsberater.
