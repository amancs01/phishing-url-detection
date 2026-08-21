"""Analyze the fixed Tier A Decision Tree rules and separation features."""

from __future__ import annotations

import json
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.tree import DecisionTreeClassifier, export_text, plot_tree

from src.build_research_tiers import TIER_A_FEATURES, build_research_tiers
from src.config import FIGURES_DIRECTORY, PROJECT_ROOT, RANDOM_STATE, RESULTS_DIRECTORY
from src.run_feature_tier_experiment import FIXED_TREE_PARAMS, PHISHING_LABEL


TREE_RULES_FILE = RESULTS_DIRECTORY / "tier_a_tree_rules.json"
TREE_ANALYSIS_FILE = PROJECT_ROOT / "research" / "tier_a_tree_analysis.md"
TREE_PREVIEW_FIGURE = FIGURES_DIRECTORY / "tier_a_tree_preview.png"
PROVENANCE_FILE = PROJECT_ROOT / "research" / "phiusiil_feature_provenance.csv"


def fit_tier_a_fixed_tree() -> tuple[DecisionTreeClassifier, Any, pd.Series, dict[str, list[int]]]:
    """Fit the exact fixed Tier A tree used in the random-split experiment."""

    tiers = build_research_tiers()
    x_tier_a = tiers.features["A"]
    y = tiers.target
    train_indices = tiers.split_indices["train"]
    model = DecisionTreeClassifier(**FIXED_TREE_PARAMS)
    model.fit(x_tier_a.loc[train_indices], y.loc[train_indices])

    return model, x_tier_a, y, tiers.split_indices


def node_records(model: DecisionTreeClassifier, feature_names: list[str]) -> list[dict[str, Any]]:
    """Return detailed node metadata from a fitted sklearn tree."""

    tree = model.tree_
    records: list[dict[str, Any]] = []

    for node_id in range(tree.node_count):
        left_child = int(tree.children_left[node_id])
        right_child = int(tree.children_right[node_id])
        feature_index = int(tree.feature[node_id])
        is_leaf = left_child == right_child
        class_counts = tree.value[node_id][0].tolist()
        predicted_class = int(model.classes_[int(tree.value[node_id][0].argmax())])

        records.append(
            {
                "node_id": int(node_id),
                "is_leaf": bool(is_leaf),
                "feature": None if is_leaf else feature_names[feature_index],
                "threshold": None if is_leaf else float(tree.threshold[node_id]),
                "left_child": None if is_leaf else left_child,
                "right_child": None if is_leaf else right_child,
                "impurity": float(tree.impurity[node_id]),
                "sample_count": int(tree.n_node_samples[node_id]),
                "weighted_sample_count": float(tree.weighted_n_node_samples[node_id]),
                "class_counts_by_model_class_order": class_counts,
                "model_class_order": [int(value) for value in model.classes_.tolist()],
                "predicted_class": predicted_class,
            }
        )

    return records


def used_features(model: DecisionTreeClassifier, feature_names: list[str]) -> list[str]:
    """Return ordered unique features used in internal nodes."""

    used: list[str] = []

    for feature_index in model.tree_.feature:
        if feature_index < 0:
            continue

        feature_name = feature_names[int(feature_index)]

        if feature_name not in used:
            used.append(feature_name)

    return used


def feature_importance_records(
    model: DecisionTreeClassifier,
    feature_names: list[str],
) -> list[dict[str, Any]]:
    """Return sorted feature-importance records."""

    table = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": model.feature_importances_,
        }
    ).sort_values(["importance", "feature"], ascending=[False, True])

    return table.to_dict(orient="records")


def provenance_lookup() -> dict[str, dict[str, Any]]:
    """Load provenance fields by feature name."""

    provenance = pd.read_csv(PROVENANCE_FILE)
    return provenance.set_index("feature_name").to_dict(orient="index")


def class_descriptive_stats(
    dataframe: pd.DataFrame,
    target: pd.Series,
    feature_names: list[str],
) -> dict[str, Any]:
    """Calculate descriptive statistics for tree-used features by class."""

    records: dict[str, Any] = {}

    for feature_name in feature_names:
        feature_stats = {}

        for label, label_name in [(0, "phishing"), (1, "legitimate")]:
            values = dataframe.loc[target == label, feature_name]
            feature_stats[label_name] = {
                "mean": float(values.mean()),
                "median": float(values.median()),
                "std": float(values.std()),
                "min": float(values.min()),
                "q05": float(values.quantile(0.05)),
                "q25": float(values.quantile(0.25)),
                "q75": float(values.quantile(0.75)),
                "q95": float(values.quantile(0.95)),
                "max": float(values.max()),
            }

        records[feature_name] = feature_stats

    return records


def evaluate_stump(
    feature_name: str,
    dataframe: pd.DataFrame,
    target: pd.Series,
    split_indices: dict[str, list[int]],
) -> dict[str, Any]:
    """Train a diagnostic decision stump for one feature."""

    model = DecisionTreeClassifier(max_depth=1, random_state=RANDOM_STATE)
    model.fit(dataframe.loc[split_indices["train"], [feature_name]], target.loc[split_indices["train"]])
    result = {
        "feature": feature_name,
        "threshold": float(model.tree_.threshold[0]),
        "validation": {},
        "test": {},
    }

    for split_name in ["validation", "test"]:
        indices = split_indices[split_name]
        y_true = target.loc[indices]
        y_pred = model.predict(dataframe.loc[indices, [feature_name]])
        result[split_name] = {
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "phishing_precision": float(
                precision_score(y_true, y_pred, pos_label=PHISHING_LABEL)
            ),
            "phishing_recall": float(
                recall_score(y_true, y_pred, pos_label=PHISHING_LABEL)
            ),
            "phishing_f1": float(f1_score(y_true, y_pred, pos_label=PHISHING_LABEL)),
        }

    return result


def stump_diagnostics(
    used_feature_names: list[str],
    dataframe: pd.DataFrame,
    target: pd.Series,
    split_indices: dict[str, list[int]],
) -> list[dict[str, Any]]:
    """Run decision-stump diagnostics for tree-used features."""

    return [
        evaluate_stump(feature_name, dataframe, target, split_indices)
        for feature_name in used_feature_names
    ]


def save_tree_preview(model: DecisionTreeClassifier, feature_names: list[str]) -> None:
    """Save a small visual preview of the Tier A tree."""

    FIGURES_DIRECTORY.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(14, 6))
    plot_tree(
        model,
        feature_names=feature_names,
        class_names=["phishing", "legitimate"],
        filled=True,
        rounded=True,
        impurity=True,
        proportion=False,
        max_depth=4,
        fontsize=8,
    )
    plt.tight_layout()
    plt.savefig(TREE_PREVIEW_FIGURE, dpi=160)
    plt.close()


def build_markdown_report(analysis: dict[str, Any]) -> str:
    """Build the human-readable Tier A tree analysis report."""

    lines = [
        "# Tier A Tree Analysis",
        "",
        "## Purpose",
        "",
        "This report investigates why the full supplied Tier A benchmark condition",
        "achieved perfect random-split test performance with a depth-4, 5-leaf",
        "Decision Tree. It does not claim data leakage; it documents the fitted",
        "tree, the features it used, and their provenance.",
        "",
        "## Fixed Configuration",
        "",
        "```text",
        "criterion = entropy",
        "max_depth = 10",
        "min_samples_leaf = 1",
        "min_samples_split = 2",
        "ccp_alpha = 0.0",
        "random_state = 42",
        "```",
        "",
        "## Root And Used Features",
        "",
        f"Root feature: `{analysis['root_feature']}`",
        "",
        "| Feature | Importance | Provenance | Directly deployable | Reference dependent | Webpage dependent |",
        "| --- | ---: | --- | --- | --- | --- |",
    ]

    provenance = analysis["used_feature_provenance"]

    for feature_name in analysis["used_features"]:
        feature_provenance = provenance[feature_name]
        importance = next(
            item["importance"]
            for item in analysis["feature_importances"]
            if item["feature"] == feature_name
        )
        lines.append(
            f"| `{feature_name}` | {importance:.6f} | "
            f"{feature_provenance['provenance_category']} | "
            f"{feature_provenance['directly_reproducible']} | "
            f"{feature_provenance['requires_reference_corpus']} | "
            f"{feature_provenance['requires_webpage_content']} |"
        )

    lines.extend(
        [
            "",
            "## Human-Readable Tree Rules",
            "",
            "```text",
            analysis["tree_rules_text"],
            "```",
            "",
            "## Top 10 Feature Importances",
            "",
            "| Rank | Feature | Importance |",
            "| ---: | --- | ---: |",
        ]
    )

    for rank, item in enumerate(analysis["feature_importances"][:10], start=1):
        lines.append(f"| {rank} | `{item['feature']}` | {item['importance']:.6f} |")

    lines.extend(
        [
            "",
            "## Decision-Stump Diagnostics",
            "",
            "Each stump uses only one tree-used feature. These are diagnostics, not",
            "model-selection results.",
            "",
            "| Feature | Threshold | Validation accuracy | Validation F1 | Test accuracy | Test F1 |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )

    for stump in analysis["stump_diagnostics"]:
        lines.append(
            f"| `{stump['feature']}` | {stump['threshold']:.6f} | "
            f"{stump['validation']['accuracy']:.6f} | "
            f"{stump['validation']['phishing_f1']:.6f} | "
            f"{stump['test']['accuracy']:.6f} | "
            f"{stump['test']['phishing_f1']:.6f} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            analysis["interpretation"],
            "",
            "## Safety Statement",
            "",
            "This analysis uses local feature matrices and saved split assignments.",
            "No URL is opened, requested, resolved, pinged, or contacted.",
        ]
    )

    return "\n".join(lines) + "\n"


def interpret_used_features(analysis: dict[str, Any]) -> str:
    """Return a cautious interpretation of the used Tier A features."""

    used = set(analysis["used_features"])

    if "URLSimilarityIndex" in used:
        return (
            "The perfect Tier A separation is primarily driven by "
            "`URLSimilarityIndex`, a URL-oriented feature classified as "
            "reference-dependent or definition-dependent rather than directly "
            "deployable. The fitted tree also uses `LineOfCode`, a "
            "webpage/content-derived feature, plus `IsHTTPS` and "
            "`NoOfSubDomain`, which are URL-text features. "
            "This supports a cautious interpretation: the random-split Tier A "
            "benchmark contains extremely discriminative supplied features, "
            "including at least one feature unavailable to a raw-URL-only "
            "deployment setting. This is not by itself proof of data leakage."
        )

    return (
        "The fitted tree does not use `URLSimilarityIndex`. Its perfect "
        "separation is therefore attributable to the listed used features and "
        "should be interpreted through their provenance categories."
    )


def run_tier_a_tree_analysis() -> dict[str, Any]:
    """Run Tier A tree analysis and save artifacts."""

    model, x_tier_a, target, split_indices = fit_tier_a_fixed_tree()
    used_feature_names = used_features(model, TIER_A_FEATURES)
    provenance = provenance_lookup()
    analysis = {
        "fixed_tree_params": FIXED_TREE_PARAMS,
        "tree_depth": int(model.get_depth()),
        "number_of_leaves": int(model.get_n_leaves()),
        "root_feature": used_feature_names[0],
        "used_features": used_feature_names,
        "node_count": int(model.tree_.node_count),
        "nodes": node_records(model, TIER_A_FEATURES),
        "tree_rules_text": export_text(
            model,
            feature_names=TIER_A_FEATURES,
            decimals=6,
        ),
        "feature_importances": feature_importance_records(model, TIER_A_FEATURES),
        "used_feature_provenance": {
            feature_name: provenance[feature_name] for feature_name in used_feature_names
        },
        "used_feature_stats_by_class": class_descriptive_stats(
            x_tier_a,
            target,
            used_feature_names,
        ),
        "stump_diagnostics": stump_diagnostics(
            used_feature_names,
            x_tier_a,
            target,
            split_indices,
        ),
        "safety_statement": (
            "Analysis used local feature matrices only; no URL was contacted."
        ),
    }
    analysis["interpretation"] = interpret_used_features(analysis)

    RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)
    TREE_ANALYSIS_FILE.parent.mkdir(parents=True, exist_ok=True)
    save_tree_preview(model, TIER_A_FEATURES)

    with TREE_RULES_FILE.open("w", encoding="utf-8") as file:
        json.dump(analysis, file, indent=2)
        file.write("\n")

    TREE_ANALYSIS_FILE.write_text(build_markdown_report(analysis), encoding="utf-8")

    return analysis


def main() -> None:
    """Run command-line Tier A tree analysis."""

    analysis = run_tier_a_tree_analysis()
    print(f"Root feature: {analysis['root_feature']}")
    print(f"Used features: {analysis['used_features']}")
    print(f"Saved: {TREE_RULES_FILE}")
    print(f"Saved: {TREE_ANALYSIS_FILE}")
    print(f"Saved: {TREE_PREVIEW_FIGURE}")


if __name__ == "__main__":
    main()
