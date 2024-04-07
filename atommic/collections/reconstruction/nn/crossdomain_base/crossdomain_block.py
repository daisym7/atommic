# coding=utf-8
__author__ = "Dimitris Karkalousos"

# Taken and adapted from: https://github.com/NKI-AI/direct/blob/main/direct/nn/crossdomain/crossdomain.py

from typing import Optional, Tuple, Union

import torch
from torch import nn

from atommic.collections.common.parts.fft import fft2, ifft2
from atommic.collections.common.parts.utils import complex_conj, complex_mul


class MultiCoil(nn.Module):
    """Makes the forward pass of multi-coil data of shape (N, N_coils, H, W, C) to a model.

    If coil_to_batch is set to True, coil dimension is moved to the batch dimension. Otherwise, it passes to the model
    each coil-data individually.
    """

    def __init__(self, model: nn.Module, coil_dim: int = 1, coil_to_batch: bool = False):
        """Inits :class:`MultiCoil`.

        Parameters
        ----------
        model : torch.nn.Module
            Any nn.Module that takes as input with 4D data (N, H, W, C). Typically, a convolutional-like model.
        coil_dim : int, optional
            Coil dimension. Default is ``1``.
        coil_to_batch : bool, optional
            If True batch and coil dimensions are merged when forwarded by the model and unmerged when outputted.
            Otherwise, input is forwarded to the model per coil. Default is ``False``.
        """
        super().__init__()
        self.model = model
        self.coil_to_batch = coil_to_batch
        self.coil_dim = coil_dim

    def _compute_model_per_coil(self, data: torch.Tensor) -> torch.Tensor:
        """Computes the model per coil."""
        output = []
        for idx in range(data.size(self.coil_dim)):
            subselected_data = data.select(self.coil_dim, idx)
            if subselected_data.shape[-1] == 2 and subselected_data.dim() == 4:
                output.append(self.model(subselected_data.permute(0, 3, 1, 2)))
            else:
                output.append(self.model(subselected_data.unsqueeze(self.coil_dim)).squeeze(self.coil_dim))
        output = torch.stack(output, dim=self.coil_dim)
        return output

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass of :class:`MultiCoil`.

        Parameters
        ----------
        x : torch.Tensor
            Input data of shape (N, N_coils, H, W, C).

        Returns
        -------
        torch.Tensor
            Output data of shape (N, N_coils, H, W, C).
        """
        if self.coil_to_batch:
            x = x.clone()

            batch, coil, channels, height, width = x.size()
            x = x.reshape(batch * coil, channels, height, width).contiguous()
            x = self.model(x).permute(0, 2, 3, 1)
            x = x.reshape(batch, coil, height, width, -1).permute(0, 1, 4, 2, 3)
        else:
            x = self._compute_model_per_coil(x).contiguous()

        return x


class CrossDomainNetwork(nn.Module):
    """Based on KIKINet implementation. Modified to work with multi-coil k-space data, as presented in [Taejoon2018]_.

    This performs optimisation in both, k-space ("K") and image ("I") domains according to domain_sequence.

    References
    ----------
    .. [Taejoon2018] Eo, Taejoon, et al. “KIKI-Net: Cross-Domain Convolutional Neural Networks for Reconstructing
        Undersampled Magnetic Resonance Images.” Magnetic Resonance in Medicine, vol. 80, no. 5, Nov. 2018, pp.
        2188–201. PubMed,  https://doi.org/10.1002/mrm.27201.
    """

    def __init__(
        self,
        image_model_list: nn.Module,
        kspace_model_list: Optional[Union[nn.Module, None]] = None,
        domain_sequence: str = "KIKI",
        image_buffer_size: int = 1,
        kspace_buffer_size: int = 1,
        normalize_image: bool = False,  # pylint: disable=unused-argument
        fft_centered: bool = False,
        fft_normalization: str = "backward",
        spatial_dims: Optional[Tuple[int, int]] = None,
        coil_dim: int = 1,
    ):
        """Inits :class:`CrossDomainNetwork`.

        Parameters
        ----------
        image_model_list : torch.nn.Module
            Image domain model list.
        kspace_model_list : torch.nn.Module, optional
            K-space domain model list. If set to None, a correction step is applied. Default is ``None``.
        domain_sequence : str, optional
            Domain sequence. Default is ``"KIKI"``.
        image_buffer_size : int, optional
            Image buffer size. Default is ``1``.
        kspace_buffer_size : int, optional
            K-space buffer size. Default is ``1``.
        normalize_image : bool, optional
            Whether to normalize the image. Default is ``False``.
        fft_centered : bool, optional
            Whether to use centered FFT. Default is ``False``.
        fft_normalization : str, optional
            Whether to normalize the FFT. Default is ``"backward"``.
        spatial_dims : Tuple[int, int], optional
            Spatial dimensions of the input. Default is ``None``.
        coil_dim : int, optional
            Coil dimension. Default is ``1``.
        """
        super().__init__()

        self.fft_centered = fft_centered
        self.fft_normalization = fft_normalization
        self.spatial_dims = spatial_dims if spatial_dims is not None else [-2, -1]
        self.coil_dim = coil_dim

        domain_sequence = list(domain_sequence.strip())  # type: ignore
        if not set(domain_sequence).issubset({"K", "I"}):
            raise ValueError(f"Invalid domain sequence. Got {domain_sequence}. Should only contain 'K' and 'I'.")
        if kspace_model_list is not None and len(kspace_model_list) != domain_sequence.count("K"):
            raise ValueError("K-space domain steps do not match k-space model list length.")
        if len(image_model_list) != domain_sequence.count("I"):
            raise ValueError("Image domain steps do not match image model list length.")

        self.domain_sequence = domain_sequence
        self.kspace_model_list = kspace_model_list
        self.kspace_buffer_size = kspace_buffer_size
        self.image_model_list = image_model_list
        self.image_buffer_size = image_buffer_size

    def kspace_correction(
        self,
        block_idx: int,
        image_buffer: torch.Tensor,
        kspace_buffer: torch.Tensor,
        sampling_mask: torch.Tensor,
        sensitivity_map: torch.Tensor,
        masked_kspace: torch.Tensor,
    ) -> torch.Tensor:
        """Performs k-space correction.

        Parameters
        ----------
        block_idx : int
            Block index.
        image_buffer : torch.Tensor
            Image buffer.
        kspace_buffer : torch.Tensor
            K-space buffer.
        sampling_mask : torch.Tensor
            Subsampling mask.
        sensitivity_map : torch.Tensor
            Coil sensitivity maps.
        masked_kspace : torch.Tensor
            Subsampled k-space.

        Returns
        -------
        torch.Tensor
            K-space buffer.
        """
        forward_buffer = [
            self._forward_operator(image.clone(), sampling_mask, sensitivity_map)
            for image in torch.split(image_buffer, 2, -1)
        ]
        forward_buffer = torch.cat(forward_buffer, -1)

        kspace_buffer = torch.cat([kspace_buffer, forward_buffer, masked_kspace], -1)

        if self.kspace_model_list is not None:
            kspace_buffer = self.kspace_model_list[block_idx](kspace_buffer.permute(0, 1, 4, 2, 3)).permute(
                0, 1, 3, 4, 2
            )
        else:
            kspace_buffer = kspace_buffer[..., :2] - kspace_buffer[..., 2:4]

        return kspace_buffer

    def image_correction(
        self,
        block_idx: int,
        image_buffer: torch.Tensor,
        kspace_buffer: torch.Tensor,
        sampling_mask: torch.Tensor,
        sensitivity_map: torch.Tensor,
    ) -> torch.Tensor:
        """Performs image space correction.

        Parameters
        ----------
        block_idx : int
            Block index.
        image_buffer : torch.Tensor
            Image buffer.
        kspace_buffer : torch.Tensor
            K-space buffer.
        sampling_mask : torch.Tensor
            Subsampling mask.
        sensitivity_map : torch.Tensor
            Coil sensitivity maps.

        Returns
        -------
        torch.Tensor
            Image buffer.
        """
        backward_buffer = [
            self._backward_operator(kspace.clone(), sampling_mask, sensitivity_map)
            for kspace in torch.split(kspace_buffer, 2, -1)
        ]
        backward_buffer = torch.cat(backward_buffer, -1)
        image_buffer = torch.cat([image_buffer, backward_buffer], -1).permute(0, 3, 1, 2)
        image_buffer = self.image_model_list[block_idx](image_buffer).permute(0, 2, 3, 1)
        return image_buffer

    def _forward_operator(
        self,
        image: torch.Tensor,
        sampling_mask: torch.Tensor,
        sensitivity_map: torch.Tensor,
    ) -> torch.Tensor:
        """Custom forward operator for the cross-domain correction.

        Parameters
        ----------
        image : torch.Tensor
            Image space. Shape [batch, coils, height, width, 2].
        sampling_mask : torch.Tensor
            Subsampling mask. Shape [batch, 1, height, width, 1].
        sensitivity_map : torch.Tensor
            Coil sensitivity maps. Shape [batch, coils, height, width, 2].

        Returns
        -------
        torch.Tensor
            K-space prediction. Shape [batch, coils, height, width, 2].
        """
        return torch.where(
            sampling_mask == 0,
            torch.tensor([0.0], dtype=image.dtype).to(image.device),
            fft2(
                complex_mul(image.unsqueeze(self.coil_dim), sensitivity_map),
                centered=self.fft_centered,
                normalization=self.fft_normalization,
                spatial_dims=self.spatial_dims,
            ).type(image.type()),
        )

    def _backward_operator(
        self,
        kspace: torch.Tensor,
        sampling_mask: torch.Tensor,
        sensitivity_map: torch.Tensor,
    ) -> torch.Tensor:
        """Custom backward operator for the cross-domain correction.

        Parameters
        ----------
        kspae : torch.Tensor
            K-space. Shape [batch, coils, height, width, 2].
        sampling_mask : torch.Tensor
            Subsampling mask. Shape [batch, 1, height, width, 1].
        sensitivity_map : torch.Tensor
            Coil sensitivity maps. Shape [batch, coils, height, width, 2].

        Returns
        -------
        torch.Tensor
            Image space prediction. Shape [batch, coils, height, width, 2].
        """
        kspace = torch.where(sampling_mask == 0, torch.tensor([0.0], dtype=kspace.dtype).to(kspace.device), kspace)
        return (
            complex_mul(
                ifft2(
                    kspace.float(),
                    centered=self.fft_centered,
                    normalization=self.fft_normalization,
                    spatial_dims=self.spatial_dims,
                ),
                complex_conj(sensitivity_map),
            )
            .sum(self.coil_dim)
            .type(kspace.type())
        )

    @staticmethod
    def crop_to_shape(x: torch.Tensor, shape: tuple) -> torch.Tensor:
        r"""Crops ``x`` to specified shape.

        Parameters
        ----------
        x : torch.Tensor
            Input tensor with shape ('\'*, H, W).
        shape : tuple
            Crop shape corresponding to H, W.

        Returns
        -------
        torch.Tensor
            Cropped tensor.
        """
        h, w = x.shape[1:3]
        if h > shape[0]:
            x = x[:, : shape[0], :, :]
        if w > shape[1]:
            x = x[:, :, : shape[1], :]
        return x

    def forward(
        self,
        masked_kspace: torch.Tensor,
        sensitivity_maps: torch.Tensor,
        sampling_mask: torch.Tensor,
    ) -> torch.Tensor:
        """Forward pass of :class:`CrossDomainNetwork`.

        Parameters
        ----------
        masked_kspace : torch.Tensor
            Subsampled k-space. Shape [batch_size, n_coils, n_x, n_y, 2]
        sensitivity_maps : torch.Tensor
            Coil sensitivity maps. Shape [batch_size, n_coils, n_x, n_y, 2]
        sampling_mask : torch.Tensor
            Subsampling mask. Shape [1, 1, n_x, n_y, 1]

        Returns
        -------
        torch.Tensor
            Reconstructed image. Shape [batch_size, n_x, n_y, 2]
        """
        input_image = self._backward_operator(masked_kspace, sampling_mask, sensitivity_maps)

        image_buffer = torch.cat([input_image] * self.image_buffer_size, -1).to(masked_kspace.device)
        kspace_buffer = torch.cat([masked_kspace] * self.kspace_buffer_size, -1).to(masked_kspace.device)

        kspace_block_idx, image_block_idx = 0, 0
        for block_domain in self.domain_sequence:
            if block_domain == "K":
                kspace_buffer = self.kspace_correction(
                    kspace_block_idx, image_buffer, kspace_buffer, sampling_mask, sensitivity_maps, masked_kspace
                )
                kspace_block_idx = kspace_block_idx + 1
            else:
                image_buffer = self.image_correction(
                    image_block_idx, image_buffer, kspace_buffer, sampling_mask, sensitivity_maps
                )
                image_buffer = self.crop_to_shape(image_buffer, sensitivity_maps.shape[2:4])
                image_block_idx = image_block_idx + 1

        return image_buffer[..., :2]
