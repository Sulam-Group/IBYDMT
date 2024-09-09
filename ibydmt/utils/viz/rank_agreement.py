from typing import Any, Mapping, Optional

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from ibydmt.utils.agreement import rank_agreement
from ibydmt.utils.config import Config
from ibydmt.utils.config import Constants as c


def viz_rank_agreement(
    config: Config,
    test_type: str,
    concept_type: str,
    pcbm: bool = False,
    workdir=c.WORKDIR,
    results_kw: Optional[Mapping[str, Any]] = None,
    ax: Optional[plt.Axes] = None,
):
    backbones, rank_agreement_results = rank_agreement(
        config,
        test_type,
        concept_type,
        pcbm=pcbm,
        workdir=workdir,
        results_kw=results_kw,
    )

    rank_agreement_mu = np.mean(rank_agreement_results, axis=0)
    rank_agreement_std = np.std(rank_agreement_results, axis=0)
    annot = np.array(
        [
            f"{mu:.2f}\n(±{std:.2f})"
            for mu, std in zip(
                rank_agreement_mu.flatten(), rank_agreement_std.flatten()
            )
        ]
    ).reshape(rank_agreement_mu.shape)

    if ax is None:
        _, ax = plt.subplots(figsize=(5, 5))

    sns.heatmap(
        rank_agreement_mu,
        vmin=-1.0,
        vmax=1.0,
        ax=ax,
        annot=annot,
        cmap="mako",
        fmt="",
        linecolor="black",
        linewidths=0.5,
        cbar_kws={"label": "Weighted Kendall's tau"},
        annot_kws={"fontsize": 7},
    )
    ax.axis("on")
    ax.tick_params(top=True, labeltop=True, bottom=False, labelbottom=False)
    ax.set_xticklabels(backbones, rotation=45, ha="left")
    ax.set_yticklabels(backbones, rotation=0)
    return backbones, rank_agreement_results
