# SoK Context Budget — Results Tables

## e1
- cell_means_pt.csv
- estimands.csv
- model_coefficients.csv
- run_summary.csv
- analysis.json: {
  "experiment_runs_dir": "/Users/mehrots/Documents/Projects/Project_ContexManagement/0.4 Experiments/runs/e1_rtk_compaction",
  "hypothesis_file": "configs/hypotheses/e1_frozen.yaml",
  "experiment": "e1_rtk_compaction",
  "factor_b": "compaction",
  "outcome_col": "pt",
  "pre_registered_model": "PT_trajectory ~ rtk + compaction + rtk:compaction + task + seed",
  "n_runs": 48,
  "status": "ok",
  "model_fit": {
    "formula": "PT_trajectory ~ rtk + factor_b + rtk:factor_b + task + seed",
    
- raw_interaction_bootstrap.json: {
  "point_estimate": 2897.4999999999927,
  "ci_low": -46983.85416666667,
  "ci_high": 50140.531249999985,
  "n_bootstrap": 1000,
  "n_blocks": 12,
  "n_obs": 48,
  "estimand": "raw_interaction",
  "pre_registered": true,
  "ci_lower": -46983.85416666667,
  "ci_upper": 50140.531249999985,
  "ci_width": 97124.38541666666
}

## e1b
- cell_means_gt.csv
- cell_means_pt.csv
- estimands.csv
- model_coefficients.csv
- run_summary.csv
- analysis.json: {
  "experiment_runs_dir": "/Users/mehrots/Documents/Projects/Project_ContexManagement/0.4 Experiments/runs/e1b_rtk_cod",
  "hypothesis_file": "configs/hypotheses/e1b_frozen.yaml",
  "experiment": "e1b_rtk_cod",
  "factor_b": "reasoning",
  "outcome_col": "gt",
  "pre_registered_model": "GT_trajectory ~ rtk + reasoning + rtk:reasoning + task + seed",
  "n_runs": 144,
  "status": "ok",
  "model_fit": {
    "formula": "PT_trajectory ~ rtk + factor_b + rtk:factor_b + task + seed",
    "outcome": "g
- raw_interaction_bootstrap.json: {
  "point_estimate": -5.055555555555486,
  "ci_low": -406.6284722222222,
  "ci_high": 374.4451388888889,
  "n_bootstrap": 1000,
  "n_blocks": 36,
  "n_obs": 144,
  "estimand": "raw_interaction",
  "pre_registered": true,
  "ci_lower": -406.6284722222222,
  "ci_upper": 374.4451388888889,
  "ci_width": 781.0736111111111
}

## e1_sensitivity
- cell_means_pt.csv
- estimands.csv
- model_coefficients.csv
- run_summary.csv
- analysis.json: {
  "experiment_runs_dir": "/Users/mehrots/Documents/Projects/Project_ContexManagement/0.4 Experiments/runs/e1_sensitivity",
  "hypothesis_file": "configs/hypotheses/e1_frozen.yaml",
  "experiment": "e1_rtk_compaction",
  "factor_b": "compaction",
  "outcome_col": "pt",
  "pre_registered_model": "PT_trajectory ~ rtk + compaction + rtk:compaction + task + seed",
  "n_runs": 72,
  "status": "ok",
  "model_fit": {
    "formula": "PT_trajectory ~ rtk + factor_b + rtk:factor_b + task + seed",
    "ou
- raw_interaction_bootstrap.json: {
  "point_estimate": NaN,
  "ci_low": NaN,
  "ci_high": NaN,
  "n_bootstrap": 1000,
  "n_blocks": 36,
  "n_obs": 72,
  "estimand": "raw_interaction",
  "pre_registered": true,
  "ci_lower": NaN,
  "ci_upper": NaN,
  "ci_width": NaN
}

## e0_anatomy
- region_breakdown.csv
- anatomy.json: [
  {
    "cell": "baseline",
    "run_id": "e1_rtk_compaction-repo_task_001-seed17-rtk0-off-standard",
    "mean_pt": 90849,
    "mean_gt": 5246,
    "peak_occupancy": 5871,
    "task_success": false
  },
  {
    "cell": "compaction_only",
    "run_id": "e1_rtk_compaction-repo_task_001-seed17-rtk0-on-standard",
    "mean_pt": 5863,
    "mean_gt": 647,
    "peak_occupancy": 1264,
    "task_success": true
  },
  {
    "cell": "baseline",
    "run_id": "e1_rtk_compaction-repo_task_001-seed52-rtk0-

## C2 metrics
- c2_metrics.csv (documented)
## C4 temporal
- c4_temporal.csv (counterfactual_illustration)
