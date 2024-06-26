import os
import pickle

import clip
import torch

from concept_lib import get_concepts


class CLIPConceptBottleneck:
    def __init__(self, config, concept_class_name=None, concept_image_idx=None):
        self.config = config

        self.concept_name, self.concepts = get_concepts(
            config,
            concept_class_name=concept_class_name,
            concept_image_idx=concept_image_idx,
        )
        self.cbm = None

    def state_path(self, workdir):
        state_dir = os.path.join(workdir, "weights", self.config.name.lower())
        os.makedirs(state_dir, exist_ok=True)
        return os.path.join(state_dir, f"clip_cbm_{self.concept_name}.pkl")

    @staticmethod
    def load_or_train(config, workdir, concept_class_name=None, concept_image_idx=None):
        model = CLIPConceptBottleneck(
            config,
            concept_class_name=concept_class_name,
            concept_image_idx=concept_image_idx,
        )
        state_path = model.state_path(workdir)

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
            model.train()
            model.save(workdir)
        return model

    def save(self, workdir):
        with open(self.state_path(workdir), "wb") as f:
            pickle.dump((self.concepts, self.cbm), f)

    def __call__(self, h):
        return h @ self.cbm.T

    @torch.no_grad()
    def train(
        self, device=torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ):
        model, _ = clip.load(self.config.data.clip_backbone, device=device)

        concepts_text = clip.tokenize(self.concepts).to(device)

        cbm = model.encode_text(concepts_text).float()
        cbm = cbm / torch.linalg.norm(cbm, dim=1, keepdim=True)
        cbm = cbm.cpu().numpy()

        self.cbm = cbm
