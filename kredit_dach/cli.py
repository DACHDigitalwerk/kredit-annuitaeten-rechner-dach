# -*- coding: utf-8 -*-
"""
Command line interface for dach-kredit.
"""

import argparse
import json
import os
import sys

try:
    from .models import LoanType, PaymentInterval, Country
    from .calculator import (
        calculate_loan,
        calculate_austria_stamp_duty,
        calculate_swiss_affordability,
    )
except ImportError:
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from kredit_dach.models import LoanType, PaymentInterval, Country
    from kredit_dach.calculator import (
        calculate_loan,
        calculate_austria_stamp_duty,
        calculate_swiss_affordability,
    )


def main():
    parser = argparse.ArgumentParser(
        description="DACH Firmenkredit-, Annuitäten- & Tilgungsplan-Rechner 2026 (PAngV, DE / AT / CH)"
    )
    parser.add_argument(
        "--amount",
        type=float,
        default=250000.0,
        help="Nettodarlehensbetrag (€ / CHF)",
    )
    parser.add_argument(
        "--interest",
        type=float,
        default=3.8,
        help="Sollzinssatz p.a. in Prozent (z. B. 3.8 für 3,8 Prozent)",
    )
    parser.add_argument(
        "--repayment",
        type=float,
        default=2.5,
        help="Anfängliche Tilgung p.a. in Prozent (z. B. 2.5 für 2,5 Prozent)",
    )
    parser.add_argument(
        "--type",
        choices=["annuity", "linear", "bullet"],
        default="annuity",
        help="Darlehensart (annuity=Annuitätendarlehen, linear=Tilgungsdarlehen, bullet=Endfällig)",
    )
    parser.add_argument(
        "--interval",
        choices=["monthly", "quarterly", "annual"],
        default="monthly",
        help="Ratenintervall (monthly=monatlich, quarterly=vierteljährlich, annual=jährlich)",
    )
    parser.add_argument(
        "--fixed-years",
        type=int,
        default=10,
        help="Zinsbindungsfrist in Jahren (z. B. 5, 10, 15, 20)",
    )
    parser.add_argument(
        "--special-repayment",
        type=float,
        default=0.0,
        help="Jährliche Sondertilgung (€ / CHF)",
    )
    parser.add_argument(
        "--country",
        choices=["DE", "AT", "CH"],
        default="DE",
        help="Ländermodus (DE=PAngV/BGB, AT=GebG Gebühr, CH=Tragbarkeit)",
    )
    parser.add_argument(
        "--property-value",
        type=float,
        default=0.0,
        help="Immobilienverkehrswert (für Schweizer Tragbarkeitsrechnung)",
    )
    parser.add_argument(
        "--gross-income",
        type=float,
        default=0.0,
        help="Jährliches Bruttoeinkommen (für Schweizer Tragbarkeitsrechnung)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Ausgabe im JSON-Format",
    )

    args = parser.parse_args()

    l_type = LoanType(args.type)
    p_interval = PaymentInterval(args.interval)

    res = calculate_loan(
        loan_amount=args.amount,
        nominal_interest_rate=args.interest / 100.0,
        initial_repayment_rate=args.repayment / 100.0,
        loan_type=l_type,
        interval=p_interval,
        fixed_interest_years=args.fixed_years,
        annual_special_repayment=args.special_repayment,
    )

    if args.country == "AT":
        at_res = calculate_austria_stamp_duty(loan_amount=args.amount)
    else:
        at_res = None

    if args.country == "CH" and args.property_value > 0 and args.gross_income > 0:
        ch_res = calculate_swiss_affordability(
            property_value=args.property_value,
            loan_amount=args.amount,
            gross_income_annual=args.gross_income,
        )
    else:
        ch_res = None

    if args.json:
        data = {
            "loan_amount": res.loan_amount,
            "nominal_interest_percent": res.nominal_interest_rate * 100,
            "effective_interest_percent": res.effective_interest_rate * 100,
            "initial_repayment_percent": res.initial_repayment_rate * 100,
            "loan_type": res.loan_type.value,
            "interval": res.interval.value,
            "fixed_interest_years": res.fixed_interest_years,
            "regular_installment": res.regular_installment,
            "annual_installment": res.annual_installment,
            "total_interest_fixed_term": res.total_interest_fixed_term,
            "total_principal_fixed_term": res.total_principal_fixed_term,
            "total_special_repayments_fixed_term": res.total_special_repayments_fixed_term,
            "remaining_balance_fixed_term": res.remaining_balance_fixed_term,
            "total_payments_fixed_term": res.total_payments_fixed_term,
            "full_amortization_years": res.full_amortization_years,
            "total_interest_full_term": res.total_interest_full_term,
            "stress_test": [s.__dict__ for s in res.stress_test],
            "austria_stamp_duty": at_res.__dict__ if at_res else None,
            "swiss_affordability": ch_res.__dict__ if ch_res else None,
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        currency = "CHF" if args.country == "CH" else "€"
        print("======================================================================")
        print("🏢 DACH FIRMENKREDIT- & TILGUNGSPLAN-RECHNER 2026")
        print("======================================================================")
        print(f"Darlehensbetrag      : {res.loan_amount:12.2f} {currency}")
        print(f"Sollzinssatz p.a.    : {res.nominal_interest_rate*100:12.2f} %")
        print(f"Effektivzins (PAngV) : {res.effective_interest_rate*100:12.2f} %")
        print(f"Anfängliche Tilgung  : {res.initial_repayment_rate*100:12.2f} %")
        print(f"Darlehensform        : {res.loan_type.label_de}")
        print(f"Zinsbindungsfrist    : {res.fixed_interest_years:12d} Jahre")
        print("----------------------------------------------------------------------")
        print(f"Regelmäßige Rate     : {res.regular_installment:12.2f} {currency} ({res.interval.value})")
        print(f"Jährliche Annuität   : {res.annual_installment:12.2f} {currency}")
        print(f"Zinsen bis Zinsende  : {res.total_interest_fixed_term:12.2f} {currency}")
        print(f"Tilgung bis Zinsende : {res.total_principal_fixed_term:12.2f} {currency}")
        if res.total_special_repayments_fixed_term > 0:
            print(f"Sondertilgungen      : {res.total_special_repayments_fixed_term:12.2f} {currency}")
        print(f"RESTSCHULD ZINSENDE  : {res.remaining_balance_fixed_term:12.2f} {currency}")
        print(f"Vollständige Tilgung : nach {res.full_amortization_years:.1f} Jahren")
        print("======================================================================")

        if at_res:
            print("\n--- 🇦🇹 ÖSTERREICH: KREDITVERTRAGSGEBÜHR (GEBG § 33 TP 8) ---")
            print(f"Gebührensatz         : {at_res.stamp_duty_rate*100:.1f} %")
            print(f"Fällige Gebühr       : {at_res.stamp_duty_amount:.2f} €")

        if ch_res:
            print("\n--- 🇨🇭 SCHWEIZ: TRAGBARKEITSRECHNUNG ---")
            print(f"Belehnung (LTV)      : {ch_res.loan_to_value_pct:.1f} %")
            print(f"Kalkulatorische Kosten: {ch_res.total_imputed_annual_cost:.2f} CHF/Jahr")
            print(f"Tragbarkeitsquote    : {ch_res.affordability_ratio_pct:.1f} % (Grenze: 33,3 %)")
            print(f"Tragbarkeit erfüllt  : {'JA ✅' if ch_res.is_affordable else 'NEIN ❌'}")


if __name__ == "__main__":
    main()
