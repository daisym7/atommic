# coding=utf-8

# Generated by CodiumAI

import pytest
import torch

from atommic.collections.common.parts.transforms import ZeroFillingPadding


class TestZeroFillingPadding:
    """Tests for :class:`ZeroFillingPadding`."""

    # Tests that zero filling is applied correctly to a tensor with shape (1, 15, 320, 320,
    # 2) and zero_filling_size=(400, 400).
    def test_happy_path_tensor_shape_15_320_320_2_zero_filling_size_400_400(self):
        data = torch.randn(1, 15, 320, 320, 2)
        zero_filling = ZeroFillingPadding(zero_filling_size=(400, 400), spatial_dims=(-2, -1))
        zero_filled_data = zero_filling(data)
        assert zero_filled_data.shape == (1, 15, 400, 400, 2)

    # Tests that zero filling is applied correctly to a tensor with shape (1, 1, 320, 320,
    # 2) and zero_filling_size=(400, 400).
    def test_happy_path_tensor_shape_1_320_320_2_zero_filling_size_400_400(self):
        data = torch.randn(1, 320, 320, 2)
        zero_filling = ZeroFillingPadding(zero_filling_size=(400, 400), spatial_dims=(-2, -1))
        zero_filled_data = zero_filling(data)
        assert zero_filled_data.shape == (1, 400, 400, 2)

    # Tests that zero filling is applied correctly to a tensor with shape (1, 15, 320, 320) and zero_filling_size=(
    # 400, 400).
    def test_happy_path_tensor_shape_15_320_320_zero_filling_size_400_400(self):
        data = torch.randn(1, 15, 320, 320)
        zero_filling = ZeroFillingPadding(zero_filling_size=(400, 400), spatial_dims=(-2, -1))
        zero_filled_data = zero_filling(data)
        assert zero_filled_data.shape == (1, 15, 400, 400)