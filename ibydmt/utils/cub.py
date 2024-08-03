import logging
import os

import numpy as np
import pandas as pd
from tqdm import tqdm

from ibydmt.utils.config import Config
from ibydmt.utils.config import Constants as c
from ibydmt.utils.data import get_dataset

logger = logging.getLogger(__name__)

rng = np.random.default_rng()


def get_confident_image_attribute_labels(config: Config, workdir=c.WORKDIR):
    logging.info("Retrieving confident image attribute labels")
    dataset = get_dataset(config, train=False)
    classes = dataset.classes

    attribute_dir = os.path.join(workdir, "data", "CUB", "attributes")
    attribute_path = os.path.join(attribute_dir, "attributes.txt")
    image_attribute_labels_path = os.path.join(
        attribute_dir, "image_attribute_labels.txt"
    )

    with open(attribute_path, "r") as f:
        attribute_idx_to_name = {int(line.split()[0]): line.split()[1] for line in f}

    image_idx = []
    class_name = []
    attribute_idx = []
    attribute_name = []
    attribute_label = []
    with open(image_attribute_labels_path, "r") as f:
        for line in tqdm(f):
            chunks = line.strip().split()
            # malformed line
            if len(chunks) != 5:
                continue

            _image_idx, _attribute_idx, _attribute_label, _confidence, _ = chunks
            if int(_confidence) >= 3:
                _image_idx = int(_image_idx)
                _attribute_idx = int(_attribute_idx)
                _attribute_name = attribute_idx_to_name[_attribute_idx]
                _attribute_label = int(_attribute_label)

                _dataset_image_idx = dataset.image_idx.index(_image_idx)
                _, _label = dataset.samples[_dataset_image_idx]
                _class_name = classes[_label]

                image_idx.append(_image_idx)
                class_name.append(_class_name)
                attribute_idx.append(_attribute_idx)
                attribute_name.append(_attribute_name)
                attribute_label.append(_attribute_label)

    df = pd.DataFrame(
        {
            "image_idx": image_idx,
            "class_name": class_name,
            "attribute_idx": attribute_idx,
            "attribute_name": attribute_name,
            "attribute_label": attribute_label,
        }
    )

    confident_image_attribute_label_path = os.path.join(
        workdir, "concept_data", "cub", "confident_image_attribute_labels.parquet"
    )
    df.to_parquet(confident_image_attribute_label_path)


def train_image_concepts(
    config: Config, concept_image_idx: int, workdir=c.WORKDIR, **kwargs
):
    dataset = get_dataset(config, train=False)
    dataset_idx_to_image_idx = dataset.image_idx

    confident_image_attribute_label_path = os.path.join(
        workdir, "concept_data", "cub", "confident_image_attribute_labels.parquet"
    )
    if not os.path.exists(confident_image_attribute_label_path):
        get_confident_image_attribute_labels(config, workdir=workdir)
    df = pd.read_parquet(confident_image_attribute_label_path)

    attribute_frequency = df.groupby("attribute_name")["attribute_label"].mean()
    attribute_class_frequency = df.groupby(["class_name", "attribute_name"])[
        "attribute_label"
    ].mean()

    image_idx = dataset_idx_to_image_idx[concept_image_idx]
    _, label = dataset.samples[concept_image_idx]
    class_name = dataset.classes[label]

    _attribute_class_frequency = attribute_class_frequency.loc[class_name]

    image_df = df[df["image_idx"] == image_idx]
    positive_attribute = image_df[image_df["attribute_label"] == 1][
        "attribute_name"
    ].values
    negative_attribute = image_df[image_df["attribute_label"] == 0][
        "attribute_name"
    ].values

    positive_attribute_score = [
        _attribute_class_frequency.loc[attribute] - attribute_frequency.loc[attribute]
        for attribute in positive_attribute
    ]
    sorted_idx = np.argsort(positive_attribute_score)[::-1]
    positive_attribute = positive_attribute[sorted_idx]

    n = config.data.num_concepts // 2
    positive_attribute = positive_attribute[:n].tolist()
    negative_attribute = rng.choice(negative_attribute, n, replace=False).tolist()
    return positive_attribute + negative_attribute
