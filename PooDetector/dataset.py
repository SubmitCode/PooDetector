# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/00_dataset.ipynb (unless otherwise specified).

__all__ = ['read_jsonl', 'base64ToImage', 'add_padding', 'span_to_box', 'jsonl_convert', 'get_labels_for_folder']

# Cell
import json
import nbdev
import re
import base64
import PIL
import pathlib
import torch
import jsonlines
from torch.utils.data import Dataset, DataLoader
from torch import nn
from io import BytesIO
from fastai.vision import *

# Cell
def read_jsonl(file_path):
    """returns a generator which returns each jsonl line.
    """
    with pathlib.Path(file_path).open('r', encoding='utf8') as f:
        for line in f:
            try:  # hack to handle broken jsonl
                str_json = json.loads(line)
                if str_json['answer'] == 'accept':
                    yield str_json
            except ValueError:
                continue

# Cell
def base64ToImage(base64_string):
    """ convert base64 string to image"""
    base64_string = base64_string[23:]
    imgdata = base64.b64decode(str(base64_string))
    image = PIL.Image.open(io.BytesIO(imgdata))
    #image = np.rollaxis(np.array(image), 2, 0)
    #image = pil2tensor(image,np.float32)
    #image.div_(255)
    #image = Image(image)
    return image

# Cell
def add_padding(image:PIL.Image, target_size=640):
    """this function adds padding so we have a rectangulare shape"""
    delta_w = target_size - image.size[0]
    delta_h = target_size - image.size[1]
    padding = (delta_w//2, delta_h//2, delta_w-(delta_w//2), delta_h-(delta_h//2))
    new_im = PIL.ImageOps.expand(image, padding)
    return new_im

# Cell
def span_to_box(jsonl:str, adjust_for_padding=0):
    """converts span data to list with points and labels"""
    box_points = []
    labels = []
    for box in jsonl['spans']:
        x1 = np.array(box['points'])[:,1].min() + adjust_for_padding
        x2 = np.array(box['points'])[:,1].max() + adjust_for_padding
        y1 = np.array(box['points'])[:,0].min()
        y2 = np.array(box['points'])[:,0].max()
        box_points.append([x1,y1,x2,y2])
        labels.append(box['label'])
    return [box_points, labels]

# Cell
def jsonl_convert(path:Path, add_pad=True):
    """convert jsonl to folder  with image files for better handling"""
    if type(path) == str:
        path = Path(path)
    path_target_fld = (path.parent / path.stem)
    path_target_fld.mkdir(parents=True, exist_ok=True)
    boxes = dict()
    for jsonl in read_jsonl(str(path)):
        base64_string = jsonl['image']
        base64_string = base64_string[23:]
        imgdata = base64.b64decode(str(base64_string))
        image = PIL.Image.open(io.BytesIO(imgdata))
        image_size = image.size
        if add_pad:
            image = add_padding(image)
        image.save(str(path_target_fld / jsonl['meta']['file']))

        adjustment = (image_size[0] - image_size[1])/2
        boxes[jsonl['meta']['file']] = span_to_box(jsonl, adjust_for_padding=adjustment)

    with open(path_target_fld / 'boxes.json', 'w') as fp:
        json.dump(boxes, fp)

    return boxes

# Cell
def get_labels_for_folder(folder:Path):
    """reads labels from boxes.json file"""
    if type(folder) is str:
        folder = Path(folder)
    with open(str(folder / 'boxes.json'), 'r') as fp:
        data = json.load(fp)
    return data