import numpy as np
import imgaug.augmenters as iaa
import logging

from .. import ROOT_LOGGER_NAME, ROOT_LOGGER_LEVEL
logger = logging.getLogger('{}.{}'.format(ROOT_LOGGER_NAME, __name__))
logger.setLevel(ROOT_LOGGER_LEVEL)


def refresh_args(f, **args_to_refresh):
    def wrapped(*args, **kwargs):
        kwargs.update(args_to_refresh)
        return f(*args, **kwargs)

    return wrapped


def get_identity_augmenter(*args, **kwargs):
    class IdentityAugmenter:
        def __init__(self):
            pass

        @staticmethod
        def augment_images(arr):
            return arr

        @staticmethod
        def augment_image(arr):
            return arr

    id_aug = IdentityAugmenter()
    return id_aug


def get_fixed_augmenter(seed=42, *args, **kwargs):
    np.random.seed(seed)
    params = {
        'flip_lr': float(np.random.randint(0, 2)),
        'if_gb_lr': float(np.random.randint(0, 2)),
        'crop': np.random.rand() * 0.2,
        'gb': np.random.rand() * 0.1,
        'contrast': 0.8 + np.random.rand() * 0.2,
        'aff_trans_x': -0.05 + np.random.rand() * 0.1,
        'aff_trans_y': -0.05 + np.random.rand() * 0.1,
        'aff_rotate': int(-10 + 20 * np.random.rand())
    }

    seq = iaa.Sequential([
        iaa.Fliplr(params['flip_lr']),
        iaa.Crop(percent=params['crop'], keep_size=True),
        iaa.Multiply(params['contrast'], per_channel=0.2),
        iaa.Affine(
            translate_percent={"x": params['aff_trans_x'], "y": params['aff_trans_y']},
            rotate=params['aff_rotate']
        )
    ])
    return seq


def get_contrast_augmentation_func(for_list=False, deterministic=False):
    seq = iaa.Sequential([
        iaa.Fliplr(0.5),
        iaa.Multiply((0.8, 1.2), per_channel=0.2),
        iaa.AdditiveGaussianNoise(loc=0, scale=(0.0, 0.01 * 255), per_channel=0.5),
    ], random_order=True)
    if deterministic:
        seq = seq.to_deterministic()
    if for_list:
        return seq.augment_images
    else:
        return seq.augment_image


def get_light_augmentation_func(for_list=False, deterministic=False):
    seq = iaa.Sequential([
        iaa.Fliplr(0.5),
        iaa.Crop(percent=(0., 0.2), keep_size=True),
        iaa.Sometimes(0.5, iaa.GaussianBlur(sigma=(0, 0.1))),
        iaa.Multiply((0.8, 1.2), per_channel=0.2),
        iaa.Affine(
            translate_percent={"x": (-0.05, 0.05), "y": (-0.05, 0.05)},
            rotate=(-15, 15)
        ),
        iaa.AdditiveGaussianNoise(loc=0, scale=(0.0, 0.01 * 255), per_channel=0.5),
    ], random_order=True)
    if deterministic:
        seq = seq.to_deterministic()
    if for_list:
        return seq.augment_images
    else:
        return seq.augment_image


def color_blur_augmentation_func(for_list=False, deterministic=False):
    seq = iaa.Sequential([
        iaa.ContrastNormalization((0.75, 1.25), per_channel=0.5),
        iaa.Sometimes(0.5, iaa.GaussianBlur(sigma=(0, .5))),
        iaa.Multiply((0.8, 1.2), per_channel=0.2),
        iaa.AdditiveGaussianNoise(loc=0, scale=(0.0, 0.02 * 255), per_channel=0.5),
    ], random_order=True)
    if deterministic:
        seq = seq.to_deterministic()
    if for_list:
        return seq.augment_images
    else:
        return seq.augment_image


def test_time_augment_image(image):
    aug1 = iaa.Pad(percent=(0., 0.2, 0.2, 0.), keep_size=True)
    aug2 = iaa.Pad(percent=(0.2, 0., 0.2, 0.), keep_size=True)
    aug3 = iaa.Pad(percent=(0.2, 0., 0., 0.2), keep_size=True)
    aug4 = iaa.Affine(rotate=15)
    aug5 = iaa.Fliplr()
    return [image] + [i.augment_image(image) for i in [aug1, aug2, aug3, aug4, aug5]]
