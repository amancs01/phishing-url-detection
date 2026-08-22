# Beyond Aggregate Accuracy: A Feature-Provenance and Cross-Dataset Generalization Audit of PhiUSIIL Phishing URL Detection

This repository contains a completed university Data Mining research project on phishing URL detection. It began as an interpretable Decision Tree URL classifier and was extended into a feature-provenance, reproducibility, domain-disjoint, and cross-dataset generalization audit.

The practical dashboard and every research script treat URLs as plain text. They do **not** open, visit, request, resolve, ping, scrape, or otherwise contact submitted or dataset URLs.

## Key Research Finding

Near-perfect within-dataset performance, even under registrable-domain-disjoint evaluation, is not sufficient evidence of robust cross-dataset phishing detection.

The frozen PhiUSIIL-trained URL-only Decision Tree achieved phishing F1 `0.996361` on a PhiUSIIL registrable-domain-disjoint split. On URL-Phish, F1 fell to `0.259245` and ROC-AUC to `0.524568`, mainly because `93,481` of `100,000` benign URLs were falsely predicted phishing.

Aggregate LegitPhish performance looked excellent, with F1 `0.995085`. However, the unseen-domain LegitPhish subgroup contained `62,990` phishing rows and only `388` legitimate rows. The model predicted every unseen-domain sample as phishing, producing F1 `0.996930` but specificity `0.000000`, balanced accuracy `0.500000`, and ROC-AUC `0.500000`. Therefore, the 99.5% aggregate LegitPhish F1 must not be interpreted alone.

## Research Motivation

Many phishing benchmarks include supplied engineered features that are not available to a deployed system receiving only a pasted URL. A model can also perform well inside one dataset but fail on another because of collection policy, source distribution, time period, domain overlap, label policy, class prevalence, or class-conditional lexical shift.

This project asks what remains after controlling those issues as much as possible in a university project:

- Which PhiUSIIL features are reproducible from raw URL text?
- How much performance survives after benchmark-only features are removed?
- Does registrable-domain-disjoint evaluation reduce performance?
- Does the frozen URL-only model transfer to independent external datasets?
- Are external results explained by overlap, class composition, or feature shift?

## Datasets

| Dataset | Role | Rows used | Phishing | Legitimate/benign | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| PhiUSIIL | Source benchmark and training dataset | 235,795 | 100,945 | 134,850 | UCI dataset 967; label `0 = phishing`, `1 = legitimate`. |
| URL-Phish Version 2 | External validation | 116,600 | 16,600 | 100,000 | Labels normalized into project convention. |
| LegitPhish Version 2 | External validation | 101,218 | 63,678 | 37,540 | One missing-label row removed from 101,219 raw rows. |

Raw datasets and generated full feature matrices are intentionally ignored and are not committed.

## Experiment Overview

The research workflow includes:

1. PhiUSIIL schema inspection and validation.
2. Safe URL-only feature extraction.
3. Feature-provenance taxonomy for PhiUSIIL supplied columns.
4. Feature reconstruction/fidelity diagnostics.
5. Tiered Decision Tree experiments:
   - Tier A: full supplied benchmark features.
   - Tier B: supplied URL-oriented features.
   - Tier C: supplied directly reproducible URL features.
   - Tier D-matched: independently reconstructed URL concepts.
   - Tier E: deployment-extended 26-feature URL-only extractor.
6. Random train/validation/test evaluation.
7. Registrable-domain-disjoint evaluation.
8. Frozen-model external validation on URL-Phish and LegitPhish.
9. Class-conditional KS feature-shift analysis.
10. Dataset-origin diagnostic trees.
11. False-positive leaf-routing diagnostics.
12. Duplicate, exact-overlap, normalized-overlap, and domain-overlap sensitivity.
13. Final empirical-conclusions lock before manuscript writing.

## Major Results

| Experiment | Key result |
| --- | --- |
| Full PhiUSIIL Tier A | Accuracy `1.000000`, F1 `1.000000`, depth `4`, leaves `5`. |
| Tier A feature dependence | Root feature `URLSimilarityIndex`; importance `0.970682`; stump F1 `0.996055`. |
| PhiUSIIL Tier E random split | Phishing F1 `0.994992`, recall `0.990622`. |
| PhiUSIIL Tier E domain-disjoint | Phishing F1 `0.996361`, recall `0.994651`. |
| URL-Phish external | Accuracy `0.196509`, precision `0.149206`, recall `0.987590`, F1 `0.259245`, ROC-AUC `0.524568`. |
| LegitPhish full external | Accuracy `0.993786`, precision `0.990219`, recall `1.000000`, F1 `0.995085`, ROC-AUC `0.991929`. |
| LegitPhish exact overlap | `36,935` exact URLs shared with PhiUSIIL; removing them gave F1 `0.995272`. |
| URL-Phish exact overlap | `595` exact URLs shared with PhiUSIIL; removing them gave F1 `0.259247`, ROC-AUC `0.521688`. |

## Careful Metric Interpretation

Phishing is the semantic positive class even though its numeric label is `0`.

Accuracy and F1 can be misleading when class composition changes. The most important example is the LegitPhish unseen-domain subset:

| Subset | Rows | Phishing | Legitimate | F1 | Specificity | Balanced accuracy | ROC-AUC |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LegitPhish unseen-domain | 63,378 | 62,990 | 388 | 0.996930 | 0.000000 | 0.500000 | 0.500000 |

The model predicted all unseen-domain rows as phishing. High F1 in this subset reflects extreme phishing prevalence, not useful two-class discrimination.

## Repository Structure

```text
phishing-url-detection/
|-- app.py
|-- data/
|   |-- external/                 # ignored raw/external data
|   |-- processed/                # ignored full matrices
|   `-- raw/                      # ignored raw PhiUSIIL data
|-- docs/
|   |-- research_presentation_outline.md
|   `-- research_viva.md
|-- models/
|   |-- model_metadata.json
|   `-- optimized_decision_tree.joblib
|-- notebooks/
|-- paper/
|   `-- phishing_url_research_paper.md
|-- reports/figures/
|-- research/
|   |-- final_empirical_conclusions.md
|   |-- literature_review.md
|   |-- paper_sections.md
|   `-- ...
|-- results/
|-- src/
|-- tests/
|-- README.md
`-- requirements.txt
```

## Installation

```powershell
git clone https://github.com/amancs01/phishing-url-detection.git
cd phishing-url-detection
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

PowerShell activation is optional:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Reproducibility

The frozen final repository already contains committed aggregate results, figures, manuscript drafts, and the packaged optimized model. To reproduce the full empirical pipeline locally, place the official raw datasets in the expected ignored locations, then run the relevant scripts.

Core PhiUSIIL preparation and internal model development:

```powershell
.\.venv\Scripts\python.exe -m src.download_data
.\.venv\Scripts\python.exe -m src.inspect_data
.\.venv\Scripts\python.exe -m src.validate_data
.\.venv\Scripts\python.exe -m src.prepare_data
.\.venv\Scripts\python.exe -m src.split_data
.\.venv\Scripts\python.exe -m src.train_baseline
.\.venv\Scripts\python.exe -m src.tune_model
.\.venv\Scripts\python.exe -m src.analyze_pruning
.\.venv\Scripts\python.exe -m src.select_model
.\.venv\Scripts\python.exe -m src.evaluate_final
```

Research audit and internal experiments:

```powershell
.\.venv\Scripts\python.exe -m src.audit_feature_fidelity
.\.venv\Scripts\python.exe -m src.analyze_feature_deltas
.\.venv\Scripts\python.exe -m src.build_research_tiers
.\.venv\Scripts\python.exe -m src.run_feature_tier_experiment
.\.venv\Scripts\python.exe -m src.analyze_tree_rules
.\.venv\Scripts\python.exe -m src.build_domain_disjoint_split
.\.venv\Scripts\python.exe -m src.run_domain_generalization_experiment
```

External validation and diagnostics:

```powershell
.\.venv\Scripts\python.exe -m src.prepare_external_data
.\.venv\Scripts\python.exe -m src.run_external_validation
.\.venv\Scripts\python.exe -m src.external_sensitivity_analysis
.\.venv\Scripts\python.exe -m src.analyze_class_conditional_shift
.\.venv\Scripts\python.exe -m src.run_dataset_origin_experiment
.\.venv\Scripts\python.exe -m src.external_overlap_sensitivity
.\.venv\Scripts\python.exe -m src.prepare_legitphish_data
.\.venv\Scripts\python.exe -m src.run_legitphish_validation
.\.venv\Scripts\python.exe -m src.compare_external_shifts
.\.venv\Scripts\python.exe -m src.audit_cross_dataset_overlap
.\.venv\Scripts\python.exe -m src.run_overlap_controlled_validation
```

These commands parse URL strings locally. They do not require users to visit phishing URLs.

## Streamlit Demo

The Streamlit dashboard demonstrates safe local inference:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The dashboard shows:

- URL text input
- phishing/legitimate prediction
- phishing probability and confidence
- extracted feature table
- model observations
- limitations and safety notes

The dashboard is an implementation output, not the primary research contribution.

## Tests

Run the full test suite:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

The final quality check for this repository passed with `96 passed, 64 warnings`. The warnings are deprecation warnings from the joblib/NumPy model-loading path.

## Safety

Forbidden operations on dataset or submitted URLs:

- HTTP requests
- browser automation
- DNS resolution
- WHOIS
- sockets
- SSL inspection
- webpage scraping
- favicon lookup
- reputation lookup

Allowed operations:

- local string parsing
- offline Public Suffix List parsing through `publicsuffix2`
- local feature extraction
- aggregate metric calculation

## Limitations

- One primary classifier family was studied.
- The Tier E feature set is URL-only but hand-engineered.
- Some PhiUSIIL feature definitions were ambiguous.
- External datasets have their own collection biases and time periods.
- Domain overlap is broader than exact URL overlap.
- LegitPhish contains substantial exact URL overlap with PhiUSIIL.
- Some subgroup metrics are heavily affected by class imbalance.
- Post-hoc diagnostics support mechanisms but do not prove causality.
- Cross-dataset validation is stronger than a random split but is not equivalent to production deployment.

## Manuscript and Submission Materials

- Main manuscript: `paper/phishing_url_research_paper.md`
- Literature review: `research/literature_review.md`
- Methodology/results draft: `research/paper_sections.md`
- Final empirical conclusions: `research/final_empirical_conclusions.md`
- Presentation outline: `docs/research_presentation_outline.md`
- Viva guide: `docs/research_viva.md`

## Citation Information

If citing this student project, use the repository title and commit/tag used for evaluation. Dataset and software citations should also cite the original dataset and tool sources.

## References

- Prasad, A., and Chandra, S. PhiUSIIL Phishing URL Dataset. UCI Machine Learning Repository. https://archive.ics.uci.edu/dataset/967/phiusiil+phishing+url+dataset
- Prasad, A., and Chandra, S. "PhiUSIIL: A diverse security profile empowered phishing URL detection framework based on similarity index and incremental learning." Computers & Security. https://doi.org/10.1016/J.COSE.2023.103545
- URL-Phish Data in Brief dataset article. https://doi.org/10.1016/j.dib.2025.112162
- LegitPhish Data in Brief dataset article. https://doi.org/10.1016/j.dib.2025.111972
- Scikit-learn documentation. https://scikit-learn.org/
- Streamlit documentation. https://docs.streamlit.io/

## Licence

The repository code is licensed under the MIT Licence. Datasets remain under their own licences and terms.
