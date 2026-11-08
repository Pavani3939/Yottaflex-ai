# YottaPay AI – Evaluation Metrics

## 1. Data Quality Metrics (from validation_summary.json)

| Metric | Description | Target |
|---|---|---|
| total_records | Total records across all entities | As generated |
| valid_records | Records passing all validation rules | ≥ 95% |
| invalid_records | Records failing any validation rule | ≤ 5% |
| duplicate_records | Intentionally injected duplicates | ~5% of invoices |
| fk_failures | Foreign key reference failures | 0 |
| arithmetic_failures | Invoice total reconciliation failures | 0 (excluding injected) |
| pk_uniqueness | Primary key collision rate | 0 |

## 2. Matching Engine Performance Metrics

Evaluated using `ground_truth.csv` as the gold standard.

| Metric | Formula | Target |
|---|---|---|
| Accuracy | (TP + TN) / Total | ≥ 90% |
| Precision | TP / (TP + FP) | ≥ 85% |
| Recall | TP / (TP + FN) | ≥ 85% |
| F1-Score | 2 × (P × R) / (P + R) | ≥ 85% |

Where:
- TP = Correctly identified matches/exceptions
- TN = Correctly identified clean invoices
- FP = Clean invoices incorrectly flagged as exceptions
- FN = Exception invoices not detected

## 3. Confusion Matrix (per exception type)

```
                    Predicted
                 MATCHED   EXCEPTION
Actual  MATCHED  [TN]      [FP]
       EXCEPTION [FN]      [TP]
```

## 4. Per-Category Breakdown

| Exception Type | Expected Count | Detected | Precision | Recall |
|---|---|---|---|---|
| Clean Matches | 70% of 2000 = ~1400 | — | — | — |
| Price Variance | 10% = ~200 | — | — | — |
| Quantity Mismatch | 8% = ~160 | — | — | — |
| Duplicate Invoice | 5% = ~100 | — | — | — |
| Missing Receipt | 4% = ~80 | — | — | — |
| Tax/Vendor Errors | 3% = ~60 | — | — | — |

(Actual values populated after engine runs.)

## 5. Reproducibility Metrics

| Check | Verification Method |
|---|---|
| Row count match | Compare CSV line counts across 2 runs |
| PK identity | MD5 of sorted ID columns |
| Checksum match | MD5/SHA256 of entire CSV files |
| Ground-truth match | Row-by-row comparison of ground_truth.csv |

All checks must pass (100% identical) with seed = 20261022.
