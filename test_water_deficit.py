import csv
import json
import math

import pytest
from water_deficit import calculate_metrics, process_batch, main


def test_reference_case():
    result = calculate_metrics(weight_kg=60, serum_sodium=166,
                               tbw_fraction=0.5)
    assert result["total_body_water_l"] == 30
    assert result["free_water_deficit_l"] == pytest.approx(30 * (166 / 140 - 1))
    assert result["estimated_sodium_change_per_l_mmol_l"] == pytest.approx(-166 / 31)


def test_target_and_fluid_electrolytes():
    result = calculate_metrics(weight_kg=70, serum_sodium=160, tbw_fraction=0.6,
                               target_sodium=150, fluid_sodium=77, fluid_potassium=20)
    assert result["free_water_deficit_l"] == pytest.approx(42 * (160 / 150 - 1))
    assert result["estimated_sodium_change_per_l_mmol_l"] == pytest.approx(-63 / 43)


@pytest.mark.parametrize("overrides", [
    {"weight_kg": 0}, {"serum_sodium": 145}, {"serum_sodium": float("nan")},
    {"tbw_fraction": 0.9}, {"target_sodium": 170},
    {"fluid_sodium": float("inf")}, {"weight_kg": True},
])
def test_invalid_input(overrides):
    params = dict(weight_kg=60, serum_sodium=166, tbw_fraction=0.5)
    params.update(overrides)
    with pytest.raises(ValueError):
        calculate_metrics(**params)


def test_batch_and_csv_formula_hardening(tmp_path):
    source, dest = tmp_path / "in.csv", tmp_path / "out.csv"
    source.write_text('label,weight_kg,serum_sodium,tbw_fraction\n'
                      '=SUM(1+1),60,166,0.5\n', encoding="utf-8")
    assert process_batch(source, dest) == 1
    with dest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["label"].startswith("'=")
    assert float(rows[0]["free_water_deficit_l"]) == pytest.approx(5.5714)


def test_batch_fails_atomically(tmp_path):
    source, dest = tmp_path / "in.csv", tmp_path / "out.csv"
    source.write_text("weight_kg,serum_sodium,tbw_fraction\n"
                      "60,166,0.5\n70,not-a-number,0.5\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Row 3"):
        process_batch(source, dest)
    assert not dest.exists()


def test_cli_json(capsys):
    assert main(["single", "--weight-kg", "60", "--serum-sodium", "166",
                 "--tbw-fraction", "0.5"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["total_body_water_l"] == 30
