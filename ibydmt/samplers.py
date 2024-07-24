from typing import Optional

import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import gaussian_kde

from ibydmt.utils.concept_data import get_dataset_with_concepts
from ibydmt.utils.config import Config


class cKDE:
    def __init__(
        self,
        config: Config,
        concept_class_name: Optional[str] = None,
        concept_image_idx: Optional[int] = None,
    ):
        ckde_config = config.ckde
        self.metric = ckde_config.get("metric", "euclidean")
        self.scale_method = ckde_config.get("scale_method", "neff")
        self.scale = ckde_config.get("scale", 2000)

        dataset = get_dataset_with_concepts(
            config,
            train=True,
            concept_class_name=concept_class_name,
            concept_image_idx=concept_image_idx,
        )
        self.semantics = dataset.semantics
        self.embedding = dataset.embedding

    def _quantile_scale(self, Z_cond_dist):
        return np.quantile(Z_cond_dist, self.scale)

    def _neff_scale(self, Z_cond_dist):
        scales = np.linspace(1e-02, 0.4, 100)[:, None]

        _Z_cond_dist = np.tile(Z_cond_dist, (len(scales), 1))

        weights = np.exp(-(_Z_cond_dist**2) / (2 * scales**2))
        neff = (np.sum(weights, axis=1) ** 2) / np.sum(weights**2, axis=1)
        diff = np.abs(neff - self.scale)
        scale_idx = np.argmin(diff)
        return scales[scale_idx].item()

    def _sample(self, z, cond_idx, m):
        sample_idx = list(set(range(len(z))) - set(cond_idx))

        kde, _ = self.kde(z, cond_idx)

        sample_z = np.tile(z, (m, 1))
        sample_z[:, sample_idx] = kde.resample(m).T

        return sample_z

    def kde(self, z, cond_idx):
        sample_idx = list(set(range(len(z))) - set(cond_idx))

        Z_sample = self.semantics[:, sample_idx]
        Z_cond = self.semantics[:, cond_idx]

        z_cond = z[cond_idx]
        Z_cond_dist = cdist(z_cond.reshape(1, -1), Z_cond, self.metric).squeeze()

        if self.scale_method == "constant":
            scale = self.scale
        if self.scale_method == "quantile":
            scale = self._quantile_scale(Z_cond_dist)
        elif self.scale_method == "neff":
            scale = self._neff_scale(Z_cond_dist)

        weights = np.exp(-(Z_cond_dist**2) / (2 * scale**2))

        return gaussian_kde(Z_sample.T, weights=weights), scale

    def nearest_neighbor(self, z):
        dist = cdist(z, self.semantics, metric=self.metric)
        return np.argmin(dist, axis=-1)

    def sample_concept(self, z, cond_idx, m=1):
        if z.ndim == 1:
            z = z.reshape(1, -1)
        return np.concatenate([self._sample(_z, cond_idx, m) for _z in z], axis=0)

    def sample_embedding(self, z, cond_idx, m=1):
        sample_z = self.sample_concept(z, cond_idx, m)
        nn_idx = self.nearest_neighbor(sample_z)
        return self.embedding[nn_idx]
