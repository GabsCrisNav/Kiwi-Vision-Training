# -*- coding: utf-8 -*-
"""yolo_nas_training

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/15pskNJp6JwET5sRqn4FdjxnU6nlMaTc7
"""

# Commented out IPython magic to ensure Python compatibility.
# %cd content

# Commented out IPython magic to ensure Python compatibility.
# %ls

! pip install ipython

!pip install super-gradients

!unzip -q ./drive/MyDrive/dataset_final.zip

# Commented out IPython magic to ensure Python compatibility.
# %rm -r __MACOSX

from super_gradients.training import Trainer
from super_gradients.training import dataloaders
from super_gradients.training.dataloaders.dataloaders import coco_detection_yolo_format_train, coco_detection_yolo_format_val
from super_gradients.training import models
from super_gradients.training.losses import PPYoloELoss
from super_gradients.training.metrics import DetectionMetrics_050
from super_gradients.training.models.detection_models.pp_yolo_e import PPYoloEPostPredictionCallback
from tqdm.auto import tqdm
from super_gradients.training import models
import os
import requests
import zipfile
import cv2
import matplotlib.pyplot as plt
import glob
import numpy as np
import random
from IPython.display import clear_output

CHECKPOINT_DIR = 'checkpoints'
trainer = Trainer(experiment_name='yolo_fruit_loops', ckpt_root_dir=CHECKPOINT_DIR)

ROOT_DIR = '/content/dataset_final'
train_imgs_dir = 'train/images'
train_labels_dir = 'train/labels'
val_imgs_dir = 'val/images'
val_labels_dir = 'val/labels'
test_imgs_dir = 'test/images'
test_labels_dir = 'test/labels'
classes = [
    "apple",
    "banana",
    "broccoli",
    "carrot",
    "mango",
    "orange",
    "peach",
    "potato",
    "strawberry",
    "tomato",
    "pepper",
    "avocado"
]

dataset_params = {
    'data_dir': ROOT_DIR,
    'train_images_dir':train_imgs_dir,
    'train_labels_dir':train_labels_dir,
    'val_images_dir':val_imgs_dir,
    'val_labels_dir':val_labels_dir,
    'test_images_dir':test_imgs_dir,
    'test_labels_dir':test_labels_dir,
    'classes': classes
}
dataset_params

train_data = coco_detection_yolo_format_train(
    dataset_params={
        'data_dir': dataset_params['data_dir'],
        'images_dir': dataset_params['train_images_dir'],
        'labels_dir': dataset_params['train_labels_dir'],
        'classes': dataset_params['classes']
    },
    dataloader_params={
        'batch_size':16,
        'num_workers':2
    }
)

val_data = coco_detection_yolo_format_val(
    dataset_params={
        'data_dir': dataset_params['data_dir'],
        'images_dir': dataset_params['val_images_dir'],
        'labels_dir': dataset_params['val_labels_dir'],
        'classes': dataset_params['classes']
    },
    dataloader_params={
        'batch_size':16,
        'num_workers':2
    }
)

test_data = coco_detection_yolo_format_val(
    dataset_params={
        'data_dir': dataset_params['data_dir'],
        'images_dir': dataset_params['test_images_dir'],
        'labels_dir': dataset_params['test_labels_dir'],
        'classes': dataset_params['classes']
    },
    dataloader_params={
        'batch_size':16,
        'num_workers':2
    }
)

clear_output()

train_data.dataset.transforms

train_data.dataset.dataset_params['transforms'][1]

train_data.dataset.dataset_params['transforms'][1]['DetectionRandomAffine']['degrees'] = 10.42

train_data.dataset.plot()

model = models.get('yolo_nas_s',
                   num_classes=len(dataset_params['classes']),
                   pretrained_weights="coco"
                   )

train_params = {
    'silent_mode': False,
    "average_best_models":True,
    "warmup_mode": "linear_epoch_step",
    "warmup_initial_lr": 1e-6,
    "lr_warmup_epochs": 3,
    "initial_lr": 5e-4,
    "lr_mode": "cosine",
    "cosine_final_lr_ratio": 0.1,
    "optimizer": "Adam",
    "optimizer_params": {"weight_decay": 0.0001},
    "zero_weight_decay_on_bias_and_bn": True,
    "ema": True,
    "ema_params": {"decay": 0.9, "decay_type": "threshold"},
    #TRAINING FOR 120 EPOCHS
    "max_epochs": 120,
    "mixed_precision": True,
    "loss": PPYoloELoss(
        use_static_assigner=False,
        # NOTE: num_classes needs to be defined here
        num_classes=len(dataset_params['classes']),
        reg_max=16
    ),
    "valid_metrics_list": [
        DetectionMetrics_050(
            score_thres=0.1,
            top_k_predictions=300,
            # NOTE: num_classes needs to be defined here
            num_cls=len(dataset_params['classes']),
            normalize_targets=True,
            post_prediction_callback=PPYoloEPostPredictionCallback(
                score_threshold=0.01,
                nms_top_k=1000,
                max_predictions=300,
                nms_threshold=0.7
            )
        )
    ],
    "metric_to_watch": 'mAP@0.50'
}

trainer.train(model=model,
              training_params=train_params,
              train_loader=train_data,
              valid_loader=val_data)

best_model = models.get('yolo_nas_s',
                        num_classes=len(dataset_params['classes']),
                        checkpoint_path="/content/drive/MyDrive/final_model/ckpt_best.pth")

trainer.test(model=best_model,
            test_loader=test_data,
            test_metrics_list=DetectionMetrics_050(score_thres=0.7,
                                                   top_k_predictions=300,
                                                   num_cls=len(dataset_params['classes']),
                                                   normalize_targets=True,
                                                   post_prediction_callback=PPYoloEPostPredictionCallback(score_threshold=0.01,
                                                                                                          nms_top_k=1000,
                                                                                                          max_predictions=300,
                                                                                                          nms_threshold=0.7)
                                                  ))

# Commented out IPython magic to ensure Python compatibility.
# %matplotlib inline
plt.close('all')

img_url = '/content/test_m.jpeg'
predict = best_model.predict(img_url, fuse_model=False)

predict.show()

class_names = predict.class_names
    labels = predict.prediction.labels
    confidence = predict.prediction.confidence
    bboxes = predict.prediction.bboxes_xyxy

    print(class_names)
    print(labels)
    print(confidence)
    print(bboxes)

    for i, (label, conf, bbox) in enumerate(zip(labels, confidence, bboxes)):
        print("prediction: ", i)
        print("label_id: ", label)
        print("label_name: ", class_names[int(label)])
        print("confidence: ", conf)
        print("bbox: ", bbox)
        print("--" * 10)

        # You can use the detection results for various tasks, such as:
        # - Filtering objects based on confidence scores or labels
        # - Analyzing object distributions within the images
        # - Calculating object dimensions or areas
        # - Implementing custom visualization techniques
        # - ...

from super_gradients.common.object_names import Models
from super_gradients.training import models

best_model.prep_model_for_conversion(input_size=[1, 3, 640, 640])
export_result = best_model.export("best_nas.onnx")

export_result

import shutil

# Source path
source_path = 'best_nas.onnx'
# Destination path
destination_path = '/content/drive/MyDrive/final_model/best_nas.onnx'

# Copy the file
shutil.copy(source_path, destination_path)

import shutil

# Source path
source_path = '/content/checkpoints/yolo_fruit_loops/RUN_20240529_030000_352166/ckpt_best.pth'
# Destination path
destination_path = '/content/drive/MyDrive/final_model/ckpt_best.pth'

# Copy the file
shutil.copy(source_path, destination_path)