"""
Confiabilidade entre dois codificadores (variável nominal).

- concordância percentual: quanto coincidem, sem descontar o acaso;
- kappa de Cohen e alfa de Krippendorff: quanto coincidem além do que o acaso daria.
"""

from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix

# Krippendorff: >= 0,80 confiável; 0,667 a 0,80 só para conclusões provisórias
BANDS = [(0.80, "confiável"), (0.667, "provisória: só para conclusões tentativas"), (-1.0, "insuficiente: revise o livro de códigos")]


def krippendorff_alpha_nominal(a: pd.Series, b: pd.Series) -> Optional[float]:
    """Alfa nominal para dois codificadores sem dados faltantes: 1 - desacordo observado / esperado."""
    values = pd.concat([a, b], ignore_index=True)
    n = len(values)               # total de valores pareáveis (2 por unidade)
    counts = values.value_counts().to_numpy(dtype=float)
    expected = n * n - (counts ** 2).sum()          # pares de valores diferentes, ao acaso
    if n < 4 or expected == 0:
        return None
    observed = 2 * int((a.to_numpy() != b.to_numpy()).sum())
    return float(1 - (n - 1) * observed / expected)


def agreement(a: pd.Series, b: pd.Series) -> Dict[str, Any]:
    """
    Concordância entre o codificador `a` e o codificador `b` (mesma ordem de unidades).
    Em `per_category`, `b` é tomado como referência para precisão e revocação de `a`.
    """
    a, b = a.astype(str).reset_index(drop=True), b.astype(str).reset_index(drop=True)
    n = len(a)
    if n == 0:
        return {"n": 0, "percent_agreement": None, "cohen_kappa": None, "krippendorff_alpha": None,
                "interpretation": None, "confusion": {"labels": [], "matrix": []}, "per_category": []}
    labels = sorted(set(a) | set(b))
    matrix = confusion_matrix(a, b, labels=labels)            # linhas = a, colunas = b
    kappa = float(cohen_kappa_score(a, b, labels=labels)) if len(labels) > 1 else None
    alpha = krippendorff_alpha_nominal(a, b)
    per_category = []
    for i, label in enumerate(labels):
        said_a, said_b, both = int(matrix[i].sum()), int(matrix[:, i].sum()), int(matrix[i, i])
        per_category.append({"category": label, "n_reference": said_b,
                             "precision": round(both / said_a, 4) if said_a else None,
                             "recall": round(both / said_b, 4) if said_b else None})
    return {
        "n": n,
        "percent_agreement": round(float((a == b).mean()), 4),
        "cohen_kappa": None if kappa is None or np.isnan(kappa) else round(kappa, 4),
        "krippendorff_alpha": None if alpha is None else round(alpha, 4),
        "interpretation": None if alpha is None else next(text for floor, text in BANDS if alpha >= floor),
        "confusion": {"labels": labels, "matrix": matrix.tolist()},
        "per_category": per_category,
    }
