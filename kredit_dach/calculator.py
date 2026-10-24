# -*- coding: utf-8 -*-
"""
Calculation engine for DACH Firmenkredit, Annuitätendarlehen, PAngV & Tilgungspläne.
"""

from typing import List, Optional
from .models import (
    LoanType,
    PaymentInterval,
    AmortizationYear,
    StressTestScenario,
    LoanResult,
    AustriaLoanResult,
    SwissMortgageResult,
)


def calculate_effective_rate_pangv(
    nominal_rate: float,
    periods_per_year: int = 12,
    disbursement_pct: float = 100.0,
    term_years: int = 10,
) -> float:
    """
    Berechnet den effektiven Jahreszins nach Preisangabenverordnung (PAngV).
    Bei 100 % Auszahlung und unterjähriger Verzinsung:
    Effektivzins = (1 + nominal / m)^m - 1
    """
    nom = max(0.0, float(nominal_rate))
    m = max(1, int(periods_per_year))
    disb = max(1.0, float(disbursement_pct)) / 100.0

    if disb < 1.0 and term_years > 0:
        # Näherungsformel für Disagio gem. PAngV
        disagio_per_year = (1.0 - disb) / term_years
        adjusted_nom = nom + disagio_per_year
        eff = ((1.0 + (adjusted_nom / m)) ** m) - 1.0
    else:
        eff = ((1.0 + (nom / m)) ** m) - 1.0

    return round(eff, 4)


def calculate_loan(
    loan_amount: float,
    nominal_interest_rate: float = 0.038,  # 3,8 % Sollzins
    initial_repayment_rate: float = 0.02,  # 2,0 % anfängliche Tilgung
    loan_type: LoanType = LoanType.ANNUITY,
    interval: PaymentInterval = PaymentInterval.MONTHLY,
    fixed_interest_years: int = 10,
    annual_special_repayment: float = 0.0,
    disbursement_pct: float = 100.0,
    max_simulation_years: int = 50,
) -> LoanResult:
    """
    Erstellt den vollständigen Tilgungsplan und die Kennzahlen für einen Firmen- oder Immobilienkredit.
    """
    amount = max(0.0, float(loan_amount))
    nominal = max(0.0, float(nominal_interest_rate))
    repayment = max(0.0, float(initial_repayment_rate))
    fixed_years = max(1, int(fixed_interest_years))
    special_rep = max(0.0, float(annual_special_repayment))
    m = interval.periods_per_year

    eff_rate = calculate_effective_rate_pangv(
        nominal_rate=nominal,
        periods_per_year=m,
        disbursement_pct=disbursement_pct,
        term_years=fixed_years,
    )

    # Regelmäßige Rate pro Intervall
    if loan_type == LoanType.ANNUITY:
        # Annuität: Zins + Tilgung
        annual_installment = amount * (nominal + repayment)
        regular_installment = annual_installment / m
    elif loan_type == LoanType.LINEAR:
        # Tilgungsdarlehen: Feste Tilgung + variable Zinsen
        annual_principal = amount * repayment
        regular_installment = (annual_principal / m) + (amount * (nominal / m))
        annual_installment = annual_principal + (amount * nominal)
    else:
        # Endfälliges Darlehen: Nur Zinsen
        annual_installment = amount * nominal
        regular_installment = annual_installment / m

    yearly_schedule: List[AmortizationYear] = []
    current_balance = amount
    total_interest_full = 0.0
    full_amort_year = float(max_simulation_years)
    loan_cleared = False

    total_interest_fixed = 0.0
    total_principal_fixed = 0.0
    total_special_fixed = 0.0
    remaining_balance_fixed = 0.0

    period_rate_nom = nominal / m

    for y in range(1, max_simulation_years + 1):
        if current_balance <= 0.0:
            if not loan_cleared:
                full_amort_year = float(y - 1)
                loan_cleared = True
            break

        opening = current_balance
        year_interest = 0.0
        year_principal = 0.0

        if loan_type == LoanType.ANNUITY:
            for _ in range(m):
                if current_balance <= 0.0:
                    break
                inter = current_balance * period_rate_nom
                p_rate = regular_installment - inter
                if current_balance - p_rate < 0.0:
                    p_rate = current_balance
                current_balance -= p_rate
                year_interest += inter
                year_principal += p_rate

        elif loan_type == LoanType.LINEAR:
            principal_per_period = (amount * repayment) / m
            for _ in range(m):
                if current_balance <= 0.0:
                    break
                inter = current_balance * period_rate_nom
                p_rate = min(current_balance, principal_per_period)
                current_balance -= p_rate
                year_interest += inter
                year_principal += p_rate

        else:  # BULLET
            year_interest = current_balance * nominal
            if y == fixed_years:
                year_principal = current_balance
                current_balance = 0.0
            else:
                year_principal = 0.0

        # Sondertilgung zum Jahresende
        actual_special = 0.0
        if current_balance > 0.0 and special_rep > 0.0 and loan_type != LoanType.BULLET:
            actual_special = min(current_balance, special_rep)
            current_balance -= actual_special

        year_total = year_interest + year_principal + actual_special
        closing = max(0.0, current_balance)

        yearly_schedule.append(
            AmortizationYear(
                year=y,
                opening_balance=round(opening, 2),
                interest_paid=round(year_interest, 2),
                principal_paid=round(year_principal, 2),
                special_repayment=round(actual_special, 2),
                total_paid=round(year_total, 2),
                closing_balance=round(closing, 2),
            )
        )

        total_interest_full += year_interest

        if y <= fixed_years:
            total_interest_fixed += year_interest
            total_principal_fixed += year_principal
            total_special_fixed += actual_special

        if y == fixed_years:
            remaining_balance_fixed = closing

    if not loan_cleared:
        full_amort_year = float(max_simulation_years)

    # Wenn Zinsbindung länger ist als die Kreditlaufzeit
    if fixed_years > len(yearly_schedule):
        remaining_balance_fixed = 0.0

    # Zinsänderungs-Stresstest für die Anschlussfinanzierung
    stress_scenarios: List[StressTestScenario] = []
    if remaining_balance_fixed > 0.0:
        base_renewal_monthly = (remaining_balance_fixed * (nominal + repayment)) / m
        for hike in (1.0, 2.0, 3.0, 4.0):
            new_nom = nominal + (hike / 100.0)
            new_annual = remaining_balance_fixed * (new_nom + repayment)
            new_monthly = new_annual / m
            diff = new_monthly - base_renewal_monthly
            extra_interest_5y = remaining_balance_fixed * (hike / 100.0) * 5.0
            stress_scenarios.append(
                StressTestScenario(
                    interest_hike_pct=hike,
                    new_interest_rate=round(new_nom * 100.0, 2),
                    new_installment=round(new_monthly, 2),
                    installment_increase=round(diff, 2),
                    total_cost_5y_hike=round(extra_interest_5y, 2),
                )
            )

    return LoanResult(
        loan_amount=round(amount, 2),
        nominal_interest_rate=round(nominal, 4),
        effective_interest_rate=round(eff_rate, 4),
        initial_repayment_rate=round(repayment, 4),
        loan_type=loan_type,
        interval=interval,
        fixed_interest_years=fixed_years,
        regular_installment=round(regular_installment, 2),
        annual_installment=round(annual_installment, 2),
        total_interest_fixed_term=round(total_interest_fixed, 2),
        total_principal_fixed_term=round(total_principal_fixed, 2),
        total_special_repayments_fixed_term=round(total_special_fixed, 2),
        remaining_balance_fixed_term=round(remaining_balance_fixed, 2),
        total_payments_fixed_term=round(
            total_interest_fixed + total_principal_fixed + total_special_fixed, 2
        ),
        full_amortization_years=round(full_amort_year, 1),
        total_interest_full_term=round(total_interest_full, 2),
        yearly_schedule=yearly_schedule,
        stress_test=stress_scenarios,
    )


def calculate_austria_stamp_duty(
    loan_amount: float,
    is_residential: bool = False,
) -> AustriaLoanResult:
    """
    Berechnet die Kreditvertragsgebühr in Österreich gem. GebG § 33 TP 8.
    Kreditverträge unterliegen 0,8 % Rechtsgeschäftsgebühr (Ausnahme: privater Wohnbau).
    """
    amount = max(0.0, float(loan_amount))
    rate = 0.0 if is_residential else 0.008
    duty = amount * rate
    return AustriaLoanResult(
        loan_amount=round(amount, 2),
        stamp_duty_rate=rate,
        stamp_duty_amount=round(duty, 2),
        is_residential_exempt=is_residential,
        euribor_margin=0.015,
    )


def calculate_swiss_affordability(
    property_value: float,
    loan_amount: float,
    gross_income_annual: float,
) -> SwissMortgageResult:
    """
    Berechnet die Schweizer Tragbarkeit einer Immobilie / Hypothek:
    - 5,0 % kalkulatorischer Zinssatz
    - 1,0 % Unterhalt und Nebenkosten
    - Amortisation der 2. Hypothek (Anteil über 66,67 %) in 15 Jahren
    - Tragbarkeit gilt als erfüllt, wenn Gesamtkosten <= 33,33 % des Bruttoeinkommens
    """
    val = max(1.0, float(property_value))
    loan = max(0.0, float(loan_amount))
    income = max(1.0, float(gross_income_annual))

    ltv = (loan / val) * 100.0

    imputed_interest = loan * 0.05
    maintenance = val * 0.01

    # 2. Hypothek: Betrag zwischen 66,67 % und max. 80 %
    limit_1st = val * (2.0 / 3.0)
    second_mortgage = max(0.0, loan - limit_1st)
    amortization_annual = second_mortgage / 15.0 if second_mortgage > 0.0 else 0.0

    total_cost = imputed_interest + maintenance + amortization_annual
    affordability_pct = (total_cost / income) * 100.0
    is_affordable = affordability_pct <= 33.333

    return SwissMortgageResult(
        property_value=round(val, 2),
        loan_amount=round(loan, 2),
        gross_income_annual=round(income, 2),
        loan_to_value_pct=round(ltv, 2),
        imputed_interest_rate=0.05,
        imputed_interest_cost=round(imputed_interest, 2),
        maintenance_cost_rate=0.01,
        maintenance_cost=round(maintenance, 2),
        amortization_cost=round(amortization_annual, 2),
        total_imputed_annual_cost=round(total_cost, 2),
        affordability_ratio_pct=round(affordability_pct, 2),
        is_affordable=is_affordable,
    )
