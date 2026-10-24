# -*- coding: utf-8 -*-
"""
DACH Firmenkredit-, Annuitäten- & Tilgungsplan-Rechner 2026.
"""

from .models import (
    LoanType,
    PaymentInterval,
    Country,
    AmortizationYear,
    StressTestScenario,
    LoanResult,
    AustriaLoanResult,
    SwissMortgageResult,
)
from .calculator import (
    calculate_effective_rate_pangv,
    calculate_loan,
    calculate_austria_stamp_duty,
    calculate_swiss_affordability,
)

__version__ = "2026.1.0"
__all__ = [
    "LoanType",
    "PaymentInterval",
    "Country",
    "AmortizationYear",
    "StressTestScenario",
    "LoanResult",
    "AustriaLoanResult",
    "SwissMortgageResult",
    "calculate_effective_rate_pangv",
    "calculate_loan",
    "calculate_austria_stamp_duty",
    "calculate_swiss_affordability",
]
