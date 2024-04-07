# coding=utf-8
__author__ = "Dimitris Karkalousos"

from typing import Sequence

import torch
from torch import nn

from atommic.collections.common.parts.fft import fft2, ifft2
from atommic.collections.common.parts.utils import coil_combination_method


class ResidualNetwork(nn.Module):
    """Residual Network, as presented in [Aggarwal2018]_, [Yaman2020]_.

    References
    ----------
    [Aggarwal2018] MoDL: Model Based Deep Learning Architecture for Inverse Problems by H.K. Aggarwal, M.P Mani, and
        Mathews Jacob in IEEE Transactions on Medical Imaging, 2018

    [Yaman2020] Yaman, B, Hosseini, SAH, Moeller, S, Ellermann, J, Uğurbil, K, Akçakaya, M. Self-supervised learning of
        physics-guided reconstruction neural networks without fully sampled reference data. Magn Reson Med. 2020; 84:
        3172– 3191. https://doi.org/10.1002/mrm.28378
    """

    def __init__(self, nb_res_blocks: int = 15, channels: int = 64, regularization_factor: float = 0.1):
        """Inits :class:`ResidualNetwork`.

        Parameters
        ----------
        nb_res_blocks : int, optional
            Number of residual blocks. Default is ``15``.
        channels : int, optional
            Number of channels. Default is ``64``.
        regularization_factor : float, optional
            Regularization factor. Default is ``0.1``.
        """
        super().__init__()
        self.relu = nn.ReLU(inplace=True)
        self.conv1 = nn.Conv2d(2, channels, kernel_size=3, stride=1, padding="same", bias=False)
        self.layers1 = nn.ModuleList()
        self.layers2 = nn.ModuleList()
        for _ in range(1, nb_res_blocks + 1):
            self.layers1.append(nn.Conv2d(channels, channels, kernel_size=3, stride=1, padding="same", bias=False))
            self.layers2.append(nn.Conv2d(channels, channels, kernel_size=3, stride=1, padding="same", bias=False))
        self.last_layer = nn.Conv2d(channels, channels, kernel_size=3, stride=1, padding="same", bias=False)
        self.final_layer = nn.Conv2d(channels, 2, kernel_size=3, stride=1, padding="same", bias=False)
        self.scaling = torch.tensor([regularization_factor]).type(torch.float32)
        self.__weights_initialization__()

    def __weights_initialization__(self):
        """Initializes the weights of the network."""
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.xavier_normal_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass of :class:`ResidualNetwork`."""
        out = self.conv1(x)
        x = out
        for i in range(len(self.layers1)):  # pylint: disable=consider-using-enumerate
            x = self.scaling.to(x.device) * self.layers2[i](self.relu(self.layers1[i](x))) + x
        x = self.last_layer(x)
        x = x + out
        return self.final_layer(x)


class ConjugateGradient(nn.Module):
    """Conjugate Gradient algorithm for solving the linear system of equations, as presented in [Aggarwal2018]_,
    [Yaman2020]_.

    References
    ----------
    [Aggarwal2018] MoDL: Model Based Deep Learning Architecture for Inverse Problems by H.K. Aggarwal, M.P Mani, and
        Mathews Jacob in IEEE Transactions on Medical Imaging, 2018

    [Yaman2020] Yaman, B, Hosseini, SAH, Moeller, S, Ellermann, J, Uğurbil, K, Akçakaya, M. Self-supervised learning of
        physics-guided reconstruction neural networks without fully sampled reference data. Magn Reson Med. 2020; 84:
        3172– 3191. https://doi.org/10.1002/mrm.28378
    """

    def __init__(
        self,
        CG_Iter: int = 10,
        mu: nn.Parameter = nn.Parameter(torch.tensor([0.05]).type(torch.float32)),
        fft_centered: bool = False,
        fft_normalization: str = "ortho",
        spatial_dims: Sequence[int] = (-2, -1),
        coil_dim: int = 1,
        coil_combination_method: str = "SENSE",
    ):
        """Inits :class:`ConjugateGradient`.

        Parameters
        ----------
        CG_Iter : int, optional
            Number of CG iterations. Default is ``10``.
        mu : torch.nn.Parameter, optional
            Regularization parameter. Default is ``0.05``.
        fft_centered : bool, optional
            Whether to center the FFT. Default is ``False``.
        fft_normalization : str, optional
            Normalization type of the FFT. Default is ``"ortho"``.
        spatial_dims : Sequence[int], optional
            Spatial dimensions of the input. Default is ``(-2, -1)``.
        coil_dim : int, optional
            Coil dimension. Default is ``1``.
        """
        super().__init__()
        self.CG_Iter = CG_Iter
        self.mu = mu
        self.fft_centered = fft_centered
        self.fft_normalization = fft_normalization
        self.spatial_dims = spatial_dims
        self.coil_dim = coil_dim
        self.coil_combination_method = coil_combination_method

    def EhE_Op(
        self, prediction: torch.Tensor, sens_maps: torch.Tensor, mask: torch.Tensor  # pylint: disable=unused-argument
    ) -> torch.Tensor:
        """This function calculates the product of the operator EhE with a given vector.

        Parameters
        ----------
        prediction : torch.Tensor
            The input vector.
        sens_maps : torch.Tensor
            The sensitivity maps.
        mask : torch.Tensor
            The undersampling mask.

        Returns
        -------
        torch.Tensor
            Data consistency term.
        """
        masked_kspace = fft2(
            prediction.unsqueeze(self.coil_dim) * sens_maps,
            self.fft_centered,
            self.fft_normalization,
            self.spatial_dims,
        )
        masked_kspace = torch.view_as_real(masked_kspace[..., 0] + 1j * masked_kspace[..., 1])
        image_space = ifft2(masked_kspace, self.fft_centered, self.fft_normalization, self.spatial_dims)
        pred = coil_combination_method(
            image_space, torch.view_as_real(sens_maps), self.coil_combination_method, self.coil_dim
        )
        pred = torch.view_as_real(pred[..., 0] + 1j * pred[..., 1])
        return torch.view_as_complex(pred) + self.mu * prediction

    def proximal_gradient(
        self,
        rsold: torch.Tensor,
        x: torch.Tensor,
        r: torch.Tensor,
        p: torch.Tensor,
        sens_maps: torch.Tensor,
        mask: torch.Tensor,
    ) -> torch.Tensor:
        """Proximal gradient descent.

        Parameters
        ----------
        rsold : torch.Tensor
            The residual.
        x : torch.Tensor
            The current estimate.
        r : torch.Tensor
            The current residual.
        p : torch.Tensor
            The current search direction.
        sens_maps : torch.Tensor
            The sensitivity maps.
        mask : torch.Tensor
            The undersampling mask.

        Returns
        -------
        torch.Tensor
            The new residual, the new estimate, the new residual, and the new search direction.
        """
        Ap = self.EhE_Op(p, sens_maps, mask)
        alpha = rsold / torch.sum(torch.conj(p) * Ap)
        alpha = alpha + 0j
        x = x + alpha * p
        r = r - alpha * Ap
        rsnew = torch.sum(torch.conj(r) * r)
        beta = rsnew / rsold
        beta = beta + 0j
        p = r + beta * p
        return rsnew, x, r, p

    def forward(self, rhs: torch.Tensor, sens_maps: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        """Forward pass of :class:`ConjugateGradient`.

        Parameters
        ----------
        rhs : torch.Tensor
            The right-hand side of the linear system.
        sens_maps : torch.Tensor
            The sensitivity maps.
        mask : torch.Tensor
            The undersampling mask.

        Returns
        -------
        torch.Tensor
            The solution of the linear system.
        """
        rhs = torch.view_as_complex(rhs)
        sens_maps = torch.view_as_complex(sens_maps)
        x = torch.zeros_like(rhs)
        i, r, p = 0, rhs, rhs
        rsold = torch.sum(torch.conj(r) * r)
        while i < self.CG_Iter:
            rsold, x, r, p = self.proximal_gradient(rsold, x, r, p, sens_maps, mask)
            i = i + 1
        return torch.view_as_real(x)
