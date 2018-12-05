from .base_preprocessor import MIMOProcessor
from ...routines.data_structure_routines import merge_dicts


class DetectionPreprocessor(MIMOProcessor):
    def __init__(self, image_getter, box_label_getter, image_augmenter, box_cropper, image_cropper, *args, **kwargs):
        """
        :param preprocessors: there must be image_getter, box_label_getter,
                                            image_augmenter, box_crop, image_cropper
        """
        super(DetectionPreprocessor, self).__init__(*args, **kwargs)
        self._image_getter = image_getter
        self._box_label_getter = box_label_getter
        self._image_aug = image_augmenter
        self._box_cropper = box_cropper
        self._image_cropper = image_cropper

    def process(self, **kwargs):
        img_getter_inp = {name: kwargs[name] for name in self._image_getter.provide_input}
        img_getter_out = self._image_getter.process(**img_getter_inp)

        box_label_getter_inp = {name: kwargs[name] for name in self._box_label_getter.provide_input}
        box_label_getter_out = self._box_label_getter.process(**box_label_getter_inp)

        box_crop_inp_full = merge_dicts(img_getter_out, box_label_getter_out)
        box_crop_inp = {name: box_crop_inp_full[name] for name in self._box_cropper.provide_input}
        box_crop_out = self._box_cropper.process(**box_crop_inp)

        img_crop_inp_full = merge_dicts(img_getter_out, box_crop_out)
        img_crop_inp = {name: img_crop_inp_full[name] for name in self._image_cropper.provide_input}
        img_crop_out = self._image_cropper.process(**img_crop_inp)

        image_aug_inp = {name: img_crop_out[name] for name in self._image_aug.provide_input}
        image_aug_out = self._image_aug.process(**image_aug_inp)

        return {k: v for k, v in merge_dicts(image_aug_out, box_crop_out).items() if k in self.provide_output}