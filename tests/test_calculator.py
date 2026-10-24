# -*- coding: utf-8 -*-
"""
Unit tests for DACH Firmenkredit- und Annuitätenrechner.
"""

import pytest
from kredit_dach.models import LoanType, PaymentInterval
from kredit_dach.calculator import (
    calculate_effective_rate_pangv,
    calculate_loan,
    calculate_austria_stamp_duty,
    calculate_swiss_affordability,
)


def test_standard_annuity_loan():
    res = calculate_loan(
        loan_amount=100000.0,
        nominal_interest_rate=0.038,  # 3,8 %
        initial_repayment_rate=0.02,  # 2,0 %
        loan_type=LoanType.ANNUITY,
        interval=PaymentInterval.MONTHLY,
        fixed_interest_years=10,
    )
    # Annual rate = 100.000 * 0.058 = 5.800 € -> Monthly = 483.33 €
    assert res.regular_installment == pytest.approx(483.33, 0.02)
    assert res.annual_installment == 5800.0
    assert res.fixed_interest_years == 10
    assert len(res.yearly_schedule) >= 10
    # Remaining balance after 10 years should be around 75.000 - 76.000 €
    assert 70000.0 < res.remaining_balance_fixed_term < 80000.0
    assert res.full_amortization_years > 20


def test_effective_rate_pangv():
    # 3.8% nominal monthly compounded
    eff = calculate_effective_rate_pangv(nominal_rate=0.038, periods_per_year=12)
    # (1 + 0.038/12)^12 - 1 ≈ 0.03867
    assert eff == pytest.approx(0.0387, 0.0005)

    # With 2% Disagio (98% payout over 10 years)
    eff_disagio = calculate_effective_rate_pangv(
        nominal_rate=0.038, periods_per_year=12, disbursement_pct=98.0, term_years=10
    )
    assert eff_disagio > eff


def test_special_repayment_effect():
    # Loan without special repayment
    res_normal = calculate_loan(
        loan_amount=200000.0,
        nominal_interest_rate=0.04,
        initial_repayment_rate=0.02,
        annual_special_repayment=0.0,
        fixed_interest_years=10,
    )
    # Loan with 5.000 € annual special repayment
    res_special = calculate_loan(
        loan_amount=200000.0,
        nominal_interest_rate=0.04,
        initial_repayment_rate=0.02,
        annual_special_repayment=5000.0,
        fixed_interest_years=10,
    )
    assert res_special.total_special_repayments_fixed_term == 50000.0
    assert res_special.remaining_balance_fixed_term < res_normal.remaining_balance_fixed_term
    assert res_special.full_amortization_years < res_normal.full_amortization_years
    assert res_special.total_interest_fixed_term < res_normal.total_interest_fixed_term


def test_linear_loan():
    # Tilgungsdarlehen
    res_lin = calculate_loan(
        loan_amount=120000.0,
        nominal_interest_rate=0.03,
        initial_repayment_rate=0.05,  # 5 % = 6.000 € / Jahr feste Tilgung
        loan_type=LoanType.LINEAR,
        fixed_interest_years=10,
    )
    assert res_lin.loan_type == LoanType.LINEAR
    # First year principal should be 6.000 €
    assert res_lin.yearly_schedule[0].principal_paid == 6000.0
    # Interest should decline year over year
    assert res_lin.yearly_schedule[1].interest_paid < res_lin.yearly_schedule[0].interest_paid


def test_bullet_loan():
    # Endfälliges Festdarlehen
    res_bullet = calculate_loan(
        loan_amount=100000.0,
        nominal_interest_rate=0.04,
        initial_repayment_rate=0.0,
        loan_type=LoanType.BULLET,
        fixed_interest_years=5,
    )
    assert res_bullet.loan_type == LoanType.BULLET
    # Years 1-4: principal = 0
    for y in range(4):
        assert res_bullet.yearly_schedule[y].principal_paid == 0.0
        assert res_bullet.yearly_schedule[y].interest_paid == 4000.0
    # Year 5: 100% principal repaid
    assert res_bullet.yearly_schedule[4].principal_paid == 100000.0


def test_quarterly_payment_interval():
    res_q = calculate_loan(
        loan_amount=100000.0,
        nominal_interest_rate=0.04,
        initial_repayment_rate=0.02,
        interval=PaymentInterval.QUARTERLY,
    )
    assert res_q.interval == PaymentInterval.QUARTERLY
    # 6.000 € per year / 4 quarters = 1.500 € per quarter
    assert res_q.regular_installment == 1500.0


def test_stress_test_scenarios():
    res = calculate_loan(
        loan_amount=300000.0,
        nominal_interest_rate=0.035,
        initial_repayment_rate=0.02,
        fixed_interest_years=10,
    )
    assert len(res.stress_test) == 4
    # Check +1%, +2%, +3%, +4%
    hikes = [s.interest_hike_pct for s in res.stress_test]
    assert hikes == [1.0, 2.0, 3.0, 4.0]
    for s in res.stress_test:
        assert s.new_installment > 0
        assert s.installment_increase > 0
        assert s.total_cost_5y_hike > 0


def test_austria_stamp_duty():
    # Commercial loan
    res_comm = calculate_austria_stamp_duty(loan_amount=500000.0, is_residential=False)
    assert res_comm.stamp_duty_rate == 0.008
    assert res_comm.stamp_duty_amount == 4000.0
    assert res_comm.is_residential_exempt is False

    # Residential loan
    res_res = calculate_austria_stamp_duty(loan_amount=500000.0, is_residential=True)
    assert res_res.stamp_duty_rate == 0.0
    assert res_res.stamp_duty_amount == 0.0
    assert res_res.is_residential_exempt is True


def test_swiss_affordability_pass():
    # 1.2M property, 800k mortgage, 200k income
    res_ch = calculate_swiss_affordability(
        property_value=1200000.0,
        loan_amount=800000.0,
        gross_income_annual=200000.0,
    )
    # LTV = 800k / 1.2M = 66.67%
    assert res_ch.loan_to_value_pct == pytest.approx(66.67, 0.02)
    # Imputed interest 5% of 800k = 40.000 CHF
    assert res_ch.imputed_interest_cost == 40000.0
    # Maintenance 1% of 1.2M = 12.000 CHF
    assert res_ch.maintenance_cost == 12000.0
    # Total = 52.000 CHF / 200.000 CHF = 26.0% <= 33.33%
    assert res_ch.affordability_ratio_pct == 26.0
    assert res_ch.is_affordable is True


def test_swiss_affordability_fail():
    # 1.0M property, 800k mortgage, 120k income
    res_ch_fail = calculate_swiss_affordability(
        property_value=1000000.0,
        loan_amount=800000.0,
        gross_income_annual=120000.0,
    )
    # Cost = 40k interest + 10k maint + (800k - 666.67k)/15 (8.89k) ≈ 58.89k
    # Ratio ≈ 58.89k / 120k ≈ 49% > 33.33%
    assert res_ch_fail.is_affordable is False
    assert res_ch_fail.affordability_ratio_pct > 33.33
