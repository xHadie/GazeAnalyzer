from PIL import Image
import math
import os
import pandas as pd
import configparser

COLOR_CODING_MOUTH = (12, 17, 252)
COLOR_CODING_FACE = (255, 0, 52)

# DETAILED
COLOR_CODING_RIGHT_EYE = (239, 12, 252)
COLOR_CODING_LEFT_EYE = (246, 252, 12)
COLOR_CODING_BETWEEN_EYE = (12, 252, 249)
COLOR_CODING_NOSE = (85, 252, 12)

config = configparser.RawConfigParser()
config.read('experiment.properties')
exp_settings = dict(config.items('EXPERIMENT_SETTINGS'))

def in_color_range(r, g, b, cond):
    # pixel value offset tolerance
    tolerance = 15
    return (cond[0] - tolerance < r < cond[0] + tolerance) and \
           (cond[1] - tolerance < g < cond[1] + tolerance) and \
           (cond[2] - tolerance < b < cond[2] + tolerance)


def resize_canvas(im, canvas_width=1024, canvas_height=768):
    """
    Resize the canvas of old_image_path.

    Store the new image in new_image_path. Center the image on the new canvas.

    Parameters
    ----------
    old_image_path : str
    new_image_path : str
    canvas_width : int
    canvas_height : int
    """
    old_width, old_height = im.size

    # Center the image
    x1 = int(math.floor((canvas_width - old_width) / 2))
    y1 = int(math.floor((canvas_height - old_height) / 2))

    mode = im.mode
    if len(mode) == 1:  # L, 1
        new_background = (255)
    if len(mode) == 3:  # RGB
        new_background = (255, 255, 255)
    if len(mode) == 4:  # RGBA, CMYK
        new_background = (255, 255, 255, 255)

    newImage = Image.new(mode, (canvas_width, canvas_height), new_background)
    newImage.paste(im, (x1, y1, x1 + old_width, y1 + old_height))
    return newImage


def init_aoi_image(session, image_id):
    aoi_image_base_path = ""

    if session == "smile":
        aoi_image_base_path = "/smile/smile_%s_%s.png"
    if session == "angry":
        aoi_image_base_path = "/angry/angry_%s_%s.png"
    if session == "yawn":
        aoi_image_base_path = "/yawning/yawning_%s_%s.png"

    aoi_image_final_path = exp.paths["AOI_DIR"] + aoi_image_base_path % (image_id, "AOI")

    image = Image.open(aoi_image_final_path)

    image = image.resize(
        (int(exp.STIMULUS_WIDTH * exp.IMAGE_SCALING),
         int(exp.STIMULUS_HEIGHT * exp.IMAGE_SCALING)))
    image = resize_canvas(image)
    return image