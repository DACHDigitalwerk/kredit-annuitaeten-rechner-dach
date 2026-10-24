# -*- coding: utf-8 -*-
import subprocess
import sys
import json
import os
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CLI_PATH = os.path.join(REPO_ROOT, "kredit_dach", "cli.py")


def _run_cli(args):
    env = os.environ.copy()
    existing_pp = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{REPO_ROOT}{os.pathsep}{existing_pp}" if existing_pp else REPO_ROOT
    cmd = [sys.executable, CLI_PATH] + args
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def test_cli_help():
    res = _run_cli(["--help"])
    assert res.returncode == 0
    assert "DACH Firmenkredit" in res.stdout


def test_cli_de_json():
    res = _run_cli([
        "--amount", "200000",
        "--interest", "3.8",
        "--repayment", "2.0",
        "--fixed-years", "10",
        "--json",
    ])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["loan_amount"] == 200000.0
    assert data["regular_installment"] == pytest.approx(966.67, 0.05)
    assert data["fixed_interest_years"] == 10
    assert len(data["stress_test"]) == 4


def test_cli_at_json():
    res = _run_cli([
        "--amount", "300000",
        "--country", "AT",
        "--json",
    ])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["austria_stamp_duty"] is not None
    assert data["austria_stamp_duty"]["stamp_duty_amount"] == 2400.0


def test_cli_ch_json():
    res = _run_cli([
        "--amount", "600000",
        "--property-value", "1000000",
        "--gross-income", "160000",
        "--country", "CH",
        "--json",
    ])
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["swiss_affordability"] is not None
    assert data["swiss_affordability"]["is_affordable"] is True
