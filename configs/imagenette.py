import os

from ibydmt.utils.config import Config, register_config


@register_config(name="imagenette")
class ImagenetteConfig(Config):
    def __init__(self):
        super().__init__()
        self.name = os.path.basename(__file__).replace(".py", "")

        data = self.data
        data.dataset = "imagenette"
        data.backbone = [
            "clip:RN50",
            "clip:ViT-B/32",
            "clip:ViT-L/14",
            "open_clip:ViT-B-32",
            "open_clip:ViT-L-14",
            "flava",
            "align",
            "blip",
        ]
        data.bottleneck = "zeroshot"
        data.classifier = "zeroshot"
        data.sampler = "ckde"
        data.num_concepts = 20

        splice = self.splice
        splice.vocab = "mscoco"
        splice.vocab_size = int(1e04)
        splice.l1_penalty = 0.20

        pcbm = self.pcbm
        pcbm.alpha = 1e-05
        pcbm.l1_ratio = 0.99

        ckde = self.ckde
        ckde.metric = "euclidean"
        ckde.scale_method = "neff"
        ckde.scale = 2000

        testing = self.testing
        testing.significance_level = 0.05
        testing.wealth = "ons"
        testing.bet = "tanh"
        testing.kernel = "rbf"
        testing.kernel_scale_method = "quantile"
        testing.kernel_scale = 0.9
        testing.tau_max = [100, 200, 400, 800, 1600]
        testing.images_per_class = 2
        testing.cardinality = [1, 2, 4]
        testing.r = 100
