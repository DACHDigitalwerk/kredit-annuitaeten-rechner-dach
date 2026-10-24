# -*- coding: utf-8 -*-
"""
Data models and Enums for DACH Firmenkredit-, Annuitäten- & Tilgungsplan-Rechner 2026.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class LoanType(str, Enum):
    """
    Kredit- und Darlehensarten.
    """
    ANNUITY = "annuity"  # Annuitätendarlehen (konstante Rate, steigende Tilgung)
    LINEAR = "linear"  # Tilgungsdarlehen (konstante Tilgung, fallende Zinsen)
    BULLET = "bullet"  # Endfälliges Darlehen (nur Zinsen, 100 % Tilgung am Ende)

    @property
    def label_de(self) -> str:
        mapping = {
            LoanType.ANNUITY: "Annuitätendarlehen (konstante Raten)",
            LoanType.LINEAR: "Tilgungsdarlehen (degressive Raten)",
            LoanType.BULLET: "Endfälliges Festdarlehen (Zinszahler)",
        }
        return mapping[self]


class PaymentInterval(str, Enum):
    """
    Zahlungsintervall der Raten.
    """
    MONTHLY = "monthly"  # 12 Raten p. a.
    QUARTERLY = "quarterly"  # 4 Raten p. a.
    ANNUAL = "annual"  # 1 Rate p. a.

    @property
    def periods_per_year(self) -> int:
        if self == PaymentInterval.MONTHLY:
            return 12
        elif self == PaymentInterval.QUARTERLY:
            return 4
        return 1


class Country(str, Enum):
    DE = "DE"  # PAngV, § 489 BGB
    AT = "AT"  # GebG § 33 TP 8, Euribor
    CH = "CH"  # SARON, Festhypothek, Tragbarkeit


@dataclass
class AmortizationYear:
    """
    Jahreszeile des Tilgungsplans.
    """
    year: int
    opening_balance: float
    interest_paid: float
    principal_paid: float
    special_repayment: float
    total_paid: float
    closing_balance: float


@dataclass
class StressTestScenario:
    """
    Szenario für Zinsanstieg bei der Anschlussfinanzierung.
    """
    interest_hike_pct: float  # z. B. +1.0 %, +2.0 %, +3.0 %, +4.0 %
    new_interest_rate: float
    new_installment: float  # Neue Rate bei gleicher Tilgungsrate
    installment_increase: float  # Mehrbelastung pro Monat / Rate
    total_cost_5y_hike: float  # Zusätzliche Zinskosten über 5 Jahre


@dataclass
class LoanResult:
    """
    Gesamtergebnis der Kreditberechnung.
    """
    loan_amount: float
    nominal_interest_rate: float  # z. B. 0.038 für 3,8 % Sollzins
    effective_interest_rate: float  # PAngV Effektivzins
    initial_repayment_rate: float  # z. B. 0.02 für 2,0 % anfängliche Tilgung
    loan_type: LoanType
    interval: PaymentInterval
    fixed_interest_years: int
    regular_installment: float  # Rate pro Intervall (z. B. Monat)
    annual_installment: float  # Rate pro Jahr
    total_interest_fixed_term: float
    total_principal_fixed_term: float
    total_special_repayments_fixed_term: float
    remaining_balance_fixed_term: float
    total_payments_fixed_term: float
    full_amortization_years: float  # Dauer bis vollständige Tilgung (Jahre)
    total_interest_full_term: float
    yearly_schedule: List[AmortizationYear] = field(default_factory=list)
    stress_test: List[StressTestScenario] = field(default_factory=list)


@dataclass
class AustriaLoanResult:
    """
    Zusatzdaten für Österreich (GebG § 33 TP 8 Kreditgebühr, etc.).
    """
    loan_amount: float
    stamp_duty_rate: float = 0.008  # 0,8 % Vergebührung gem. GebG § 33 TP 8
    stamp_duty_amount: float = 0.0  # Fällige Rechtsgeschäftsgebühr
    is_residential_exempt: bool = False  # Bei privatem Wohnbau oft befreit
    euribor_margin: float = 0.015  # Typische Aufschlagsmarge (z. B. 1,5 %)


@dataclass
class SwissMortgageResult:
    """
    Schweizer Hypotheken- und Tragbarkeitsrechnung.
    """
    property_value: float
    loan_amount: float  # Hypothek
    gross_income_annual: float
    loan_to_value_pct: float  # Belehnung (Hypothek / Verkehrswert * 100)
    imputed_interest_rate: float = 0.05  # 5,0 % kalkulatorischer Zins
    imputed_interest_cost: float = 0.0
    maintenance_cost_rate: float = 0.01  # 1,0 % Unterhalts- und Nebenkosten
    maintenance_cost: float = 0.0
    amortization_cost: float = 0.0  # 2. Hypothek in 15 Jahren auf 66,67 %
    total_imputed_annual_cost: float = 0.0
    affordability_ratio_pct: float = 0.0  # Kosten / Bruttoeinkommen * 100
    is_affordable: bool = False  # True wenn Tragbarkeit <= 33.33 %
