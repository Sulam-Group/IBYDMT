import logging
import os

import numpy as np
from torch.utils.data import Dataset

from ibydmt.bottlenecks import get_bottleneck
from ibydmt.utils.concepts import get_concepts
from ibydmt.utils.config import Config
from ibydmt.utils.config import Constants as c
from ibydmt.utils.data import get_dataset, get_embedded_dataset

logger = logging.getLogger(__name__)


def get_dataset_with_concepts(
    config: Config,
    train=True,
    concept_class_name=None,
    concept_image_idx=None,
    workdir=c.WORKDIR,
):
    return DatasetWithConcepts(
        config,
        train=train,
        concept_class_name=concept_class_name,
        concept_image_idx=concept_image_idx,
        workdir=workdir,
    )


class DatasetWithConcepts(Dataset):
    def __init__(
        self,
        config: Config,
        train=True,
        concept_class_name=None,
        concept_image_idx=None,
        workdir=c.WORKDIR,
        device=c.DEVICE,
    ):
        super().__init__()
        dataset = get_embedded_dataset(config, train=train, workdir=workdir)
        self.classes = dataset.classes
        self.concept_name, self.concepts = get_concepts(
            config,
            workdir=workdir,
            concept_class_name=concept_class_name,
            concept_image_idx=concept_image_idx,
        )

        op = dataset.op
        root = os.path.join(workdir, "concept_data")
        data_dir = os.path.join(root, config.data.dataset.lower())
        data_path = os.path.join(
            data_dir, f"{op}_{config.backbone_name()}_{self.concept_name}.npy"
        )
        if not os.path.exists(data_path):
            os.makedirs(data_dir, exist_ok=True)

            bottleneck = get_bottleneck(
                config,
                concept_class_name=concept_class_name,
                concept_image_idx=concept_image_idx,
                workdir=workdir,
            )
            semantics = bottleneck.encode_dataset(
                train=train, workdir=workdir, device=device
            )
            np.save(data_path, semantics)

        self.embedding = dataset.embedding
        self.semantics = np.load(data_path)
        self.label = dataset.label

    def __len__(self):
        return self.semantics.shape[0]

    def __getitem__(self, idx):
        return self.semantics[idx], self.label[idx]
