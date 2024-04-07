# coding=utf-8
# Generated by CodiumAI
import numpy as np
import pytest
import torch

from atommic.collections.common.data.subsample import (
    Equispaced1DMaskFunc,
    Equispaced2DMaskFunc,
    Gaussian1DMaskFunc,
    Gaussian2DMaskFunc,
    Poisson2DMaskFunc,
    Random1DMaskFunc,
    create_masker,
)


class TestCreateMasker:
    # Tests that the function returns an Equispaced1DMaskFunc object for valid input parameters.
    def test_returns_equispaced1d_mask_func(self):
        mask_type_str = "equispaced1d"
        center_fractions = [0.3, 0.7]
        accelerations = [8, 6]

        mask_func = create_masker(mask_type_str, center_fractions, accelerations)

        assert isinstance(mask_func, Equispaced1DMaskFunc)

    # Tests that the function returns an Equispaced2DMaskFunc object for valid input parameters.
    def test_returns_equispaced2d_mask_func(self):
        mask_type_str = "equispaced2d"
        center_fractions = [0.3, 0.7]
        accelerations = [8, 6]

        mask_func = create_masker(mask_type_str, center_fractions, accelerations)

        assert isinstance(mask_func, Equispaced2DMaskFunc)

    # Tests that the function returns a Gaussian1DMaskFunc object for valid input parameters.
    def test_returns_gaussian1d_mask_func(self):
        mask_type_str = "gaussian1d"
        center_fractions = [0.3, 0.7]
        accelerations = [8, 6]

        mask_func = create_masker(mask_type_str, center_fractions, accelerations)

        assert isinstance(mask_func, Gaussian1DMaskFunc)

    # Tests that the function returns a Gaussian2DMaskFunc object for valid input parameters.
    def test_returns_gaussian2d_mask_func(self):
        mask_type_str = "gaussian2d"
        center_fractions = [0.3, 0.7]
        accelerations = [8, 6]

        mask_func = create_masker(mask_type_str, center_fractions, accelerations)

        assert isinstance(mask_func, Gaussian2DMaskFunc)

    # Tests that the function returns a Poisson2DMaskFunc object for valid input parameters.
    def test_returns_poisson2d_mask_func(self):
        mask_type_str = "poisson2d"
        center_fractions = [0.3, 0.7]
        accelerations = [8.0, 6.0]

        mask_func = create_masker(mask_type_str, center_fractions, accelerations)

        assert isinstance(mask_func, Poisson2DMaskFunc)

    # Tests that the function returns a Random1DMaskFunc object for valid input parameters.
    def test_returns_random_mask_func(self):
        mask_type_str = "random1d"
        center_fractions = [0.5]
        accelerations = [4]

        mask_func = create_masker(mask_type_str, center_fractions, accelerations)

        assert isinstance(mask_func, Random1DMaskFunc)

    # Tests that the function raises a NotImplementedError for an unsupported mask type.
    def test_raises_not_implemented_error(self):
        mask_type_str = "unsupported"
        center_fractions = [0.3, 0.7]
        accelerations = [8, 6]

        with pytest.raises(NotImplementedError):
            create_masker(mask_type_str, center_fractions, accelerations)


class TestEquispaced1DMaskFunc:
    # Tests that the code correctly generates a sub-sampling mask of the given shape.
    def test_generate_sub_sampling_mask(self):
        shape = (1, 10, 10)
        accelerations = [4]
        center_fractions = [0.08]
        mask_func = Equispaced1DMaskFunc(center_fractions, accelerations)
        mask, acceleration = mask_func(shape)
        assert mask.shape[1] == shape[1]
        assert acceleration == accelerations[0]
        assert isinstance(mask, torch.Tensor)

    # Tests that the code correctly generates a sub-sampling mask of the given shape for multiple accelerations.
    def test_generate_sub_sampling_mask_mul_acc(self):
        shape = (1, 10, 10)
        accelerations = [4, 8]
        center_fractions = [0.08, 0.04]
        mask_func = Equispaced1DMaskFunc(center_fractions, accelerations)
        mask, acceleration = mask_func(shape)
        assert mask.shape[1] == shape[1]
        assert acceleration in accelerations
        assert isinstance(mask, torch.Tensor)

    # Tests that the code is generated with partial Fourier.
    def test_generate_equispaced_mask_with_partial_fourier(self):
        shape = (1, 10, 10)
        accelerations = [4]
        center_fractions = [0.08]
        partial_fourier_percentage = 0.5
        mask_func = Equispaced1DMaskFunc(center_fractions, accelerations)
        mask, _ = mask_func(shape, partial_fourier_percentage=partial_fourier_percentage)
        assert torch.sum(mask) > 0

    # Tests that the code selects the correct number of low-frequency columns based on the center fraction.
    def test_select_low_frequency_columns(self):
        shape = (1, 10, 10)
        accelerations = [6]
        center_fractions = [0.03]
        mask_func = Equispaced1DMaskFunc(center_fractions, accelerations)
        mask, _ = mask_func(shape)
        num_cols = shape[-2]
        center_fraction = mask_func.center_fractions[0]
        num_low_freqs = int(round(num_cols * center_fraction))
        assert torch.sum(mask[:, :num_low_freqs]) == num_low_freqs


class TestEquispaced2DMaskFunc:
    # Tests that the code correctly generates a sub-sampling mask of the given shape.
    def test_generate_sub_sampling_mask(self):
        shape = (1, 10, 10)
        accelerations = [4]
        center_fractions = [0.08]
        mask_func = Equispaced2DMaskFunc(center_fractions, accelerations)
        mask, acceleration = mask_func(shape)
        assert mask.shape[:1] == shape[:1]
        assert acceleration == accelerations[0]
        assert isinstance(mask, torch.Tensor)

    # Tests that the code correctly generates a sub-sampling mask of the given shape for multiple accelerations.
    def test_generate_sub_sampling_mask_mul_acc(self):
        shape = (1, 10, 10)
        accelerations = [4, 8]
        center_fractions = [0.08, 0.04]
        mask_func = Equispaced2DMaskFunc(center_fractions, accelerations)
        mask, acceleration = mask_func(shape)
        assert mask.shape[:1] == shape[:1]
        assert acceleration in accelerations
        assert isinstance(mask, torch.Tensor)

    # Tests that the code is generated with partial Fourier.
    def test_generate_equispaced_mask_with_partial_fourier(self):
        shape = (1, 10, 10)
        accelerations = [4]
        center_fractions = [0.08]
        partial_fourier_percentage = 0.5
        mask_func = Equispaced2DMaskFunc(center_fractions, accelerations)
        mask, _ = mask_func(shape, partial_fourier_percentage=partial_fourier_percentage)
        assert torch.sum(mask) > 0

    # Tests that the code selects the correct number of low-frequency columns based on the center fraction.
    def test_select_low_frequency_columns(self):
        shape = (1, 10, 10)
        accelerations = [6]
        center_fractions = [0.03]
        mask_func = Equispaced2DMaskFunc(center_fractions, accelerations)
        mask, _ = mask_func(shape)
        num_cols = shape[-2]
        center_fraction = mask_func.center_fractions[0]
        num_low_freqs = int(round(num_cols * center_fraction))
        assert torch.sum(mask[:, :num_low_freqs]) == num_low_freqs


class TestGaussian1DMaskFunc:
    # Tests that the code correctly generates a sub-sampling mask of the given shape.
    def test_generate_sub_sampling_mask(self):
        shape = (1, 10, 10)
        accelerations = [4]
        center_fractions = [0.7]
        mask_func = Gaussian1DMaskFunc(center_fractions, accelerations)
        mask, acceleration = mask_func(shape)
        assert mask.shape[1] == shape[1]
        assert acceleration == accelerations[0]
        assert isinstance(mask, torch.Tensor)

    # Tests that the code correctly generates a sub-sampling mask of the given shape for multiple accelerations.
    def test_generate_sub_sampling_mask_mul_acc(self):
        shape = (1, 10, 10)
        accelerations = [4, 8]
        center_fractions = [0.7, 0.7]
        mask_func = Gaussian1DMaskFunc(center_fractions, accelerations)
        mask, acceleration = mask_func(shape)
        assert mask.shape[1] == shape[1]
        assert acceleration in accelerations
        assert isinstance(mask, torch.Tensor)

    # Tests that the code is generated with partial Fourier.
    def test_generate_gaussian_mask_with_partial_fourier(self):
        shape = (1, 10, 10)
        accelerations = [4]
        center_fractions = [0.7]
        partial_fourier_percentage = 0.2
        mask_func = Gaussian1DMaskFunc(center_fractions, accelerations)
        mask, _ = mask_func(shape, partial_fourier_percentage=partial_fourier_percentage)
        assert torch.sum(mask) > 0

    # Tests that the code defines the center scale.
    def test_define_center_scale(self):
        shape = (1, 10, 10)
        accelerations = [4]
        center_fractions = [0.7]
        mask_func = Gaussian1DMaskFunc(center_fractions, accelerations)
        scale = 0.5
        mask, _ = mask_func(shape, scale=scale)
        assert torch.sum(mask) > 0
        scale = 0.01
        mask, _ = mask_func(shape, scale=scale)
        assert torch.sum(mask) > 0


class TestGaussian2DMaskFunc:
    # Tests that the code correctly generates a sub-sampling mask of the given shape.
    def test_generate_sub_sampling_mask(self):
        shape = (1, 10, 10)
        accelerations = [4]
        center_fractions = [0.7]
        mask_func = Gaussian2DMaskFunc(center_fractions, accelerations)
        mask, acceleration = mask_func(shape)
        assert mask.shape[:1] == shape[:1]
        assert acceleration == accelerations[0]
        assert isinstance(mask, torch.Tensor)

    # Tests that the code correctly generates a sub-sampling mask of the given shape for multiple accelerations.
    def test_generate_sub_sampling_mask_mul_acc(self):
        shape = (1, 10, 10)
        accelerations = [4, 8]
        center_fractions = [0.7, 0.7]
        mask_func = Gaussian2DMaskFunc(center_fractions, accelerations)
        mask, acceleration = mask_func(shape)
        assert mask.shape[:1] == shape[:1]
        assert acceleration in accelerations
        assert isinstance(mask, torch.Tensor)

    # Tests that the Gaussian mask is generated with partial Fourier.
    def test_generate_gaussian_mask_with_partial_fourier(self):
        shape = (1, 10, 10)
        accelerations = [4]
        center_fractions = [0.7]
        partial_fourier_percentage = 0.5
        mask_func = Gaussian2DMaskFunc(center_fractions, accelerations)
        mask, _ = mask_func(shape, partial_fourier_percentage=partial_fourier_percentage)
        assert torch.sum(mask) > 0

    # Tests that the code defines the center scale.
    def test_define_center_scale(self):
        shape = (1, 10, 10)
        accelerations = [4]
        center_fractions = [0.7]
        mask_func = Gaussian2DMaskFunc(center_fractions, accelerations)
        scale = 0.5
        mask, _ = mask_func(shape, scale=scale)
        assert torch.sum(mask) > 0
        scale = 0.01
        mask, _ = mask_func(shape, scale=scale)
        assert torch.sum(mask) > 0


class TestPoisson2DMaskFunc:
    # Tests that the code correctly generates a sub-sampling mask of the given shape.
    def test_generate_sub_sampling_mask(self):
        shape = (10, 10, 2)
        accelerations = [4]
        center_fractions = [0.7]
        tolerance = 1.0
        mask_func = Poisson2DMaskFunc(center_fractions, accelerations)
        mask, acceleration = mask_func(shape, tol=tolerance)
        assert mask.shape[1:-1] == shape[:-1]
        assert acceleration == accelerations[0]
        assert isinstance(mask, torch.Tensor)

    # Tests that the code correctly generates a sub-sampling mask of the given shape for multiple accelerations.
    def test_generate_sub_sampling_mask_mul_acc(self):
        shape = (10, 10, 2)
        accelerations = [4, 10]
        center_fractions = [0.7, 0.7]
        tolerance = 1.0
        mask_func = Poisson2DMaskFunc(center_fractions, accelerations)
        mask, acceleration = mask_func(shape, tol=tolerance)
        assert mask.shape[1:-1] == shape[:-1]
        assert acceleration in accelerations
        assert isinstance(mask, torch.Tensor)

    # Tests that the Poisson mask is generated with partial Fourier.
    def test_generate_poisson_mask_with_partial_fourier(self):
        shape = (10, 10, 2)
        accelerations = [4]
        center_fractions = [0.7]
        partial_fourier_percentage = 0.5
        tolerance = 1.0
        mask_func = Poisson2DMaskFunc(center_fractions, accelerations)
        mask, _ = mask_func(shape, partial_fourier_percentage=partial_fourier_percentage, tol=tolerance)
        assert torch.sum(mask) > 0

    # Tests that the Poisson mask is generated with calibration.
    def test_generate_poisson_mask_with_calibration(self):
        shape = (10, 10, 2)
        accelerations = [4]
        center_fractions = [0.7]
        calibration_percentage = 0.5
        tolerance = 1.0
        mask_func = Poisson2DMaskFunc(center_fractions, accelerations)
        mask, _ = mask_func(shape, calib=(calibration_percentage, calibration_percentage), tol=tolerance)
        assert torch.sum(mask) > 0

    # Tests that the Poisson mask is generated without cropped corner.
    def test_generate_poisson_mask_without_cropped_corner(self):
        shape = (10, 10, 2)
        accelerations = [4]
        center_fractions = [0.7]
        tolerance = 1.0
        mask_func = Poisson2DMaskFunc(center_fractions, accelerations)
        mask, _ = mask_func(shape, crop_corner=False, tol=tolerance)
        assert torch.sum(mask) > 0

    # Tests that the Poisson mask is generated with the specified tolerance value.
    def test_generate_poisson_mask_with_tolerance_value(self):
        shape = (10, 10, 2)
        accelerations = [4]
        center_fractions = [0.7]
        tolerance = 1.0
        mask_func = Poisson2DMaskFunc(center_fractions, accelerations)
        mask, _ = mask_func(shape, tol=tolerance)
        assert torch.sum(mask) > 0

    # Tests that the Poisson mask is generated with maximum attempts.
    def test_generate_poisson_mask_with_max_attempts(self):
        shape = (10, 10, 2)
        accelerations = [3]
        center_fractions = [0.7]
        max_attempts = 1
        tolerance = 1.0
        mask_func = Poisson2DMaskFunc(center_fractions, accelerations)
        mask, _ = mask_func(shape, max_attempts=max_attempts, tol=tolerance)
        assert torch.sum(mask) > 0

    # Tests that the code defines the center scale.
    def test_define_center_scale(self):
        shape = (10, 10, 2)
        accelerations = [4]
        center_fractions = [0.7]
        mask_func = Poisson2DMaskFunc(center_fractions, accelerations)
        tolerance = 1.0
        scale = 0.5
        mask, _ = mask_func(shape, scale=scale, tol=tolerance)
        assert torch.sum(mask) > 0
        scale = 0.01
        mask, _ = mask_func(shape, scale=scale, tol=tolerance)
        assert torch.sum(mask) > 0


class TestRandom1DMaskFunc:
    """Tests that the code correctly generates a Random sub-sampling mask of the given shape."""

    def test_generate_sub_sampling_mask(self):
        shape = (1, 10, 10)
        accelerations = [4]
        center_fractions = [0.08]
        mask_func = Random1DMaskFunc(center_fractions, accelerations)
        mask, acceleration = mask_func(shape)
        assert mask.shape[1] == shape[1]
        assert acceleration == accelerations[0]
        assert isinstance(mask, torch.Tensor)

    # Tests that the code correctly generates a sub-sampling mask of the given shape for multiple accelerations.
    def test_generate_sub_sampling_mask_mul_acc(self):
        shape = (1, 10, 10)
        accelerations = [4, 8]
        center_fractions = [0.08, 0.04]
        mask_func = Random1DMaskFunc(center_fractions, accelerations)
        mask, acceleration = mask_func(shape)
        assert mask.shape[1] == shape[1]
        assert acceleration in accelerations
        assert isinstance(mask, torch.Tensor)

    # Tests that the code is generated with partial Fourier.
    def test_generate_random_mask_with_partial_fourier(self):
        shape = (1, 10, 10)
        accelerations = [4]
        center_fractions = [0.08]
        partial_fourier_percentage = 0.5
        mask_func = Random1DMaskFunc(center_fractions, accelerations)
        mask, _ = mask_func(shape, partial_fourier_percentage=partial_fourier_percentage)
        assert torch.sum(mask) > 0

    # Tests that the code selects the correct number of low-frequency columns based on the center fraction.
    def test_select_low_frequency_columns(self):
        shape = (1, 10, 10)
        accelerations = [6]
        center_fractions = [0.03]
        mask_func = Random1DMaskFunc(center_fractions, accelerations)
        mask, _ = mask_func(shape)
        num_cols = shape[-2]
        center_fraction = mask_func.center_fractions[0]
        num_low_freqs = int(round(num_cols * center_fraction))
        assert torch.sum(mask[:, :num_low_freqs]) == num_low_freqs