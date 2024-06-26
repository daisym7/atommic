# coding=utf-8
__author__ = "Dimitris Karkalousos"

import torch
from omegaconf import DictConfig

from atommic.collections.segmentation.nn.attentionunet_base.attentionunet_block import AttentionUnet
from atommic.collections.segmentation.nn.segmentationnet import BaseSegmentationNet

__all__ = ["SegmentationAttentionUNet"]


# type: ignore
class SegmentationAttentionUNet(BaseSegmentationNet):
    """Implementation of the Attention UNet for MRI segmentation, as presented in [Oktay2018]_.

    References
    ----------
    .. [Oktay2018] O. Oktay, J. Schlemper, L.L. Folgoc, M. Lee, M. Heinrich, K. Misawa, K. Mori, S. McDonagh, N.Y.
        Hammerla, B. Kainz, B. Glocker, D. Rueckert. Attention U-Net: Learning Where to Look for the Pancreas. 2018.
        https://arxiv.org/abs/1804.03999

    """

    def build_segmentation_module(self, cfg: DictConfig) -> torch.nn.Module:
        """Build the segmentation module.

        Parameters
        ----------
        cfg : DictConfig
            Configuration object specifying the model's hyperparameters.

        Returns
        -------
        torch.nn.Module
            The segmentation module.
        """
        return AttentionUnet(
            in_chans=self.input_channels,
            out_chans=cfg.get("segmentation_module_output_channels", 2),
            chans=cfg.get("segmentation_module_channels", 64),
            num_pool_layers=cfg.get("segmentation_module_pooling_layers", 2),
            drop_prob=cfg.get("segmentation_module_dropout", 0.0),
        )
