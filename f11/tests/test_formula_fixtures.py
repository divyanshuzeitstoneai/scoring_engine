"""
Automated Test Suite for All Hand-Computed Fixtures (Section 5 & 6).
Loads and asserts all 276 YAML fixtures in f11/fixtures/formula/ against:
1. Hand-computed expected values
2. Reference implementation (evaluate_order_reference)
3. Production engine (F11Engine)
Verifies exact match across full output row with zero floating point arithmetic.
"""

import glob
import os
import yaml
import pytest
from decimal import Decimal
from typing import Dict, Any

from f11.engine.formula import F11Engine
from f11.reference.reference_formula import evaluate_order_reference

FIXTURES_DIR = "f11/fixtures/formula"
fixture_files = sorted(glob.glob(os.path.join(FIXTURES_DIR, "*.yaml")))


@pytest.fixture(scope="module")
def configs():
    def load_cfg(path: str):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    base = load_cfg("f11/config/f11.config.yaml")
    balanced = load_cfg("f11/config/profiles/balanced.yaml")
    strict = load_cfg("f11/config/profiles/strict.yaml")
    lenient = load_cfg("f11/config/profiles/lenient.yaml")
    
    # Ensure packaging_cost defaults to 0 in base test configs
    base["packaging_cost"] = 0
    balanced["packaging_cost"] = 0
    half_even = dict(balanced)
    half_even["rounding_mode"] = "half_even"
    return {
        "balanced": balanced,
        "strict": strict,
        "lenient": lenient,
        "half_even": half_even,
        "default": base
    }


def load_fixture_data(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.mark.parametrize("file_path", fixture_files, ids=[os.path.basename(f).replace(".yaml", "") for f in fixture_files])
def test_individual_fixture_exactness(file_path: str, configs):
    fdata = load_fixture_data(file_path)
    f_id = fdata["id"]
    profile_name = fdata.get("profile", "balanced")
    cfg = configs.get(profile_name, configs["balanced"])
    
    order = fdata["input"]
    expected = fdata["expected"]
    
    # 1. Run Engine
    engine = F11Engine(cfg)
    eng_res = engine.evaluate_order(order)
    
    # 2. Run Reference Implementation
    ref_res = evaluate_order_reference(order, cfg)
    
    # Check exclusion
    if expected.get("lane") == "EXCLUDED" or expected.get("classification") == "excluded":
        assert eng_res["lane"] == "EXCLUDED", f"{f_id}: Engine failed to exclude"
        assert ref_res.lane == "EXCLUDED", f"{f_id}: Reference failed to exclude"
        if expected.get("exclusion_reason"):
            assert eng_res["exclusion_reason"] == expected["exclusion_reason"]
            assert ref_res.exclusion_reason == expected["exclusion_reason"]
        return

    # 3. Assert Core Financial Quantities (exact integer minor units)
    assert eng_res["L"] == expected["L"], f"{f_id}: L mismatch (engine={eng_res['L']}, exp={expected['L']})"
    assert ref_res.L == expected["L"], f"{f_id}: Reference L mismatch"
    
    assert eng_res["D"] == expected["D"], f"{f_id}: D mismatch (engine={eng_res['D']}, exp={expected['D']})"
    assert ref_res.D == expected["D"], f"{f_id}: Reference D mismatch"
    
    assert eng_res["R"] == expected["R"], f"{f_id}: R mismatch (engine={eng_res['R']}, exp={expected['R']})"
    assert ref_res.R == expected["R"], f"{f_id}: Reference R mismatch"
    
    assert eng_res["Sc"] == expected["Sc"], f"{f_id}: Sc mismatch (engine={eng_res['Sc']}, exp={expected['Sc']})"
    assert ref_res.Sc == expected["Sc"], f"{f_id}: Reference Sc mismatch"
    
    assert eng_res["C"] == expected["C"], f"{f_id}: C mismatch (engine={eng_res['C']}, exp={expected['C']})"
    assert ref_res.C == expected["C"], f"{f_id}: Reference C mismatch"

    if expected.get("COGS") is not None:
        assert eng_res["COGS"] == expected["COGS"], f"{f_id}: COGS mismatch"
        assert ref_res.COGS == expected["COGS"], f"{f_id}: Reference COGS mismatch"
    else:
        assert eng_res["COGS"] is None, f"{f_id}: Expected COGS None, got {eng_res['COGS']}"
        assert ref_res.COGS is None, f"{f_id}: Reference Expected COGS None"

    if expected.get("S") is not None:
        assert eng_res["S"] == expected["S"], f"{f_id}: S mismatch"
        assert ref_res.S == expected["S"], f"{f_id}: Reference S mismatch"
    else:
        assert eng_res["S"] is None, f"{f_id}: Expected S None"
        assert ref_res.S is None, f"{f_id}: Reference Expected S None"

    if expected.get("G") is not None:
        assert eng_res["G"] == expected["G"], f"{f_id}: G mismatch"
        assert ref_res.G == expected["G"], f"{f_id}: Reference G mismatch"
    else:
        assert eng_res["G"] is None, f"{f_id}: Expected G None"
        assert ref_res.G is None, f"{f_id}: Reference Expected G None"

    assert eng_res["E"] == expected["E"], f"{f_id}: E mismatch (engine={eng_res['E']}, exp={expected['E']})"
    assert ref_res.E == expected["E"], f"{f_id}: Reference E mismatch"
    
    assert eng_res["O"] == expected["O"], f"{f_id}: O mismatch"
    assert ref_res.O == expected["O"], f"{f_id}: Reference O mismatch"

    # 4. Assert Profit and P_upper
    if expected.get("P") is not None:
        assert eng_res["P"] == expected["P"], f"{f_id}: P mismatch (engine={eng_res['P']}, exp={expected['P']})"
        assert ref_res.P == expected["P"], f"{f_id}: Reference P mismatch"
    else:
        assert eng_res["P"] is None, f"{f_id}: Expected P None"
        assert ref_res.P is None, f"{f_id}: Reference Expected P None"

    if expected.get("P_upper") is not None:
        assert eng_res["P_upper"] == expected["P_upper"], f"{f_id}: P_upper mismatch"
        assert ref_res.P_upper == expected["P_upper"], f"{f_id}: Reference P_upper mismatch"

    # 5. Assert Margin and Classifications
    if expected.get("lane"):
        assert eng_res["lane"] == expected["lane"], f"{f_id}: Lane mismatch (engine={eng_res['lane']}, exp={expected['lane']})"
        assert ref_res.lane == expected["lane"], f"{f_id}: Reference Lane mismatch"

    if expected.get("band"):
        assert eng_res["band"] == expected["band"], f"{f_id}: Band mismatch"
        assert ref_res.band == expected["band"], f"{f_id}: Reference Band mismatch"

    if expected.get("classification"):
        assert eng_res["classification"] == expected["classification"], f"{f_id}: Classification mismatch"
        assert ref_res.classification == expected["classification"], f"{f_id}: Reference Classification mismatch"

    # 6. Top Loss Driver
    if "top_loss_driver" in expected and expected["top_loss_driver"] is not None:
        assert eng_res["top_loss_driver"] == expected["top_loss_driver"], f"{f_id}: Top loss driver mismatch"
        assert ref_res.top_loss_driver == expected["top_loss_driver"], f"{f_id}: Reference Top loss driver mismatch"
