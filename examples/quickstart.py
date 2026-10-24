# -*- coding: utf-8 -*-
"""
Quickstart Example: DACH Firmenkredit-, Annuitäten- & Tilgungsplan-Rechner 2026.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from kredit_dach import (
    calculate_loan,
    calculate_austria_stamp_duty,
    calculate_swiss_affordability,
    LoanType,
    PaymentInterval,
)


def main():
    print("--- 1. Gewerbekredit / Annuitätendarlehen Deutschland ---")
    loan = calculate_loan(
        loan_amount=250000.0,
        nominal_interest_rate=0.038,  # 3,8 % Sollzins
        initial_repayment_rate=0.025,  # 2,5 % Tilgung
        loan_type=LoanType.ANNUITY,
        interval=PaymentInterval.MONTHLY,
        fixed_interest_years=10,
        annual_special_repayment=5000.0,  # 5.000 € jährliche Sondertilgung
    )
    print(f"Kreditsumme          : {loan.loan_amount:10.2f} €")
    print(f"Monatliche Rate      : {loan.regular_installment:10.2f} €")
    print(f"Effektivzins (PAngV) : {loan.effective_interest_rate*100:10.2f} %")
    print(f"Restschuld n. 10 J.  : {loan.remaining_balance_fixed_term:10.2f} €")
    print(f"Zinsen in Zinsbindung: {loan.total_interest_fixed_term:10.2f} €")
    print(f"Volltilgung erreicht : nach {loan.full_amortization_years:.1f} Jahren")

    print("\n--- 2. Zins-Stresstest für die Anschlussfinanzierung (+2 %) ---")
    scenario_2pct = next(s for s in loan.stress_test if s.interest_hike_pct == 2.0)
    print(f"Neuer Zinssatz       : {scenario_2pct.new_interest_rate:.2f} %")
    print(f"Neue monatliche Rate : {scenario_2pct.new_installment:.2f} € (Mehrbelastung: +{scenario_2pct.installment_increase:.2f} €/Mo.)")
    print(f"Zusätzliche Zinskosten 5J: +{scenario_2pct.total_cost_5y_hike:.2f} €")

    print("\n--- 3. Österreich: Kreditvertragsgebühr gem. GebG § 33 TP 8 ---")
    at_duty = calculate_austria_stamp_duty(loan_amount=250000.0, is_residential=False)
    print(f"Gebühr auf Kreditvertrag (0,8 %): {at_duty.stamp_duty_amount:.2f} €")

    print("\n--- 4. Schweiz: Tragbarkeitsprüfung (SARON & Festhypothek) ---")
    ch_calc = calculate_swiss_affordability(
        property_value=1200000.0,
        loan_amount=800000.0,
        gross_income_annual=190000.0,
    )
    print(f"Belehnung (LTV)      : {ch_calc.loan_to_value_pct:.1f} %")
    print(f"Kalkulatorische Kosten: {ch_calc.total_imputed_annual_cost:.2f} CHF/Jahr")
    print(f"Tragbarkeit (<= 33,3 %): {ch_calc.affordability_ratio_pct:.1f} % -> {'ERFÜLLT ✅' if ch_calc.is_affordable else 'NICHT ERFÜLLT ❌'}")


if __name__ == "__main__":
    main()
