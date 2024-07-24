import logging
import os
import pickle

import clip
import torch

from ibydmt.utils.concepts import get_concepts
from ibydmt.utils.config import Config
from ibydmt.utils.config import Constants as c

logger = logging.getLogger(__name__)


class CLIPConceptBottleneck:
    def __init__(
        self,
        config: Config,
        workdir=c.WORKDIR,
        concept_class_name=None,
        concept_image_idx=None,
    ):
        self.config = config

        self.concept_name, self.concepts = get_concepts(
            config,
            workdir=workdir,
            concept_class_name=concept_class_name,
            concept_image_idx=concept_image_idx,
        )
        self.cbm = None

    def state_path(self, workdir=c.WORKDIR):
        state_dir = os.path.join(workdir, "weights", self.config.name.lower())
        os.makedirs(state_dir, exist_ok=True)
        return os.path.join(state_dir, f"clip_cbm_{self.concept_name}.pkl")

    @staticmethod
    def load_or_train(
        config: Config,
        workdir=c.WORKDIR,
        concept_class_name=None,
        concept_image_idx=None,
        device=c.DEVICE,
    ):
        model = CLIPConceptBottleneck(
            config,
            workdir=workdir,
            concept_class_name=concept_class_name,
            concept_image_idx=concept_image_idx,
        )
        state_path = model.state_path(workdir=workdir)

        cbm_exists = os.path.exists(state_path)
        if cbm_exists:
            with open(state_path, "rb") as f:
                concepts, _ = pickle.load(f)

            if concepts != model.concepts:
                cbm_exists = False

        if cbm_exists:
            with open(state_path, "rb") as f:
                _, cbm = pickle.load(f)
            model.cbm = cbm
        else:
            model.train(device=device)
            model.save(workdir)
        return model

    def save(self, workdir=c.WORKDIR):
        with open(self.state_path(workdir=workdir), "wb") as f:
            pickle.dump((self.concepts, self.cbm), f)

    def __call__(self, h):
        return h @ self.cbm.T

    @torch.no_grad()
    def train(self, device=c.DEVICE):
        logger.info(
            f"Training CLIP CBM for dataset {self.config.data.dataset.lower()}"
            f" and concept_name = {self.concept_name}"
        )
        model, _ = clip.load(self.config.data.clip_backbone, device=device)

        concepts_text = clip.tokenize(self.concepts).to(device)

        cbm = model.encode_text(concepts_text).float()
        cbm = cbm / torch.linalg.norm(cbm, dim=1, keepdim=True)
        cbm = cbm.cpu().numpy()

        self.cbm = cbm