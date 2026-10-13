import test from "node:test";
import assert from "node:assert/strict";
import { calculateMetrics } from "../web/calculator.mjs";

test("reference adult female calculation", () => {
  const r = calculateMetrics({ weight_kg: 60, serum_sodium: 166, tbw_fraction: 0.5 });
  assert.equal(r.total_body_water_l, 30);
  assert.ok(Math.abs(r.free_water_deficit_l - 5.5714285714) < 1e-8);
  assert.ok(Math.abs(r.estimated_sodium_change_per_l_mmol_l + 166/31) < 1e-8);
});
test("custom target and infusate", () => {
  const r = calculateMetrics({ weight_kg: 70, serum_sodium: 160, tbw_fraction: 0.6,
    target_sodium: 150, fluid_sodium: 77, fluid_potassium: 20 });
  assert.ok(Math.abs(r.free_water_deficit_l - 2.8) < 1e-8);
  assert.ok(Math.abs(r.estimated_sodium_change_per_l_mmol_l + 63/43) < 1e-8);
});
test("non-finite and clinically inconsistent input rejected", () => {
  const base = { weight_kg: 60, serum_sodium: 166, tbw_fraction: 0.5 };
  for (const overrides of [
    { weight_kg: 0 }, { serum_sodium: 145 }, { serum_sodium: Number.NaN },
    { tbw_fraction: 0.9 }, { target_sodium: 170 },
    { fluid_sodium: Infinity }, { weight_kg: true }
  ]) assert.throws(() => calculateMetrics({ ...base, ...overrides }), RangeError);
});
