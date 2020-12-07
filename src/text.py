import logging

from imutils.object_detection import non_max_suppression
import numpy as np
import time
import cv2
import os
import re
import shutil
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'c:\Program Files\Tesseract-OCR\tesseract.exe'
from fuzzywuzzy import fuzz


WIDTH = 320
HEIGHT = 320
MIN_CONFIDENCE = 0.5
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
MODEL = os.path.join(SCRIPT_DIR, "frozen_east_text_detection.pb")


def is_jpg(path: str) -> bool:
    with open(path, "rb") as f:
        buf = f.read(4)
    for sign in ['ffd8']:  # , '89504e47']:
        if buf.startswith(bytearray.fromhex(sign)):
            return True
    return False


class TextDetector:
    def __init__(self):
        # load the pre-trained EAST text detector
        print("[INFO] loading EAST text detector...")
        self._net = cv2.dnn.readNet(MODEL)

    def detect(self, path):
        if not is_jpg(path):
            return False

        # load the input image and grab the image dimensions
        image = cv2.imread(path)
        # orig = image.copy()
        (H, W) = image.shape[:2]

        # set the new width and height and then determine the ratio in change
        # for both the width and height
        # (newW, newH) = (WIDTH, HEIGHT)
        if W > H:
            newW = min(1024, (W // 32) * 32)
            newH = round(newW * (H / W))
            newH = (newH// 32) * 32
        else:
            newH = min(1024, (H // 32) * 32)
            newW = round(newH * (W / H))
            newW = (newW // 32) * 32
        # rW = W / float(newW)
        # rH = H / float(newH)

        # resize the image and grab the new image dimensions
        image = cv2.resize(image, (newW, newH))
        (H, W) = image.shape[:2]
        print("{}x{}".format(H, W))

        # define the two output layer names for the EAST detector model that
        # we are interested -- the first is the output probabilities and the
        # second can be used to derive the bounding box coordinates of text
        layerNames = [
            "feature_fusion/Conv_7/Sigmoid",
            "feature_fusion/concat_3"]

        # # load the pre-trained EAST text detector
        # print("[INFO] loading EAST text detector...")
        # net = cv2.dnn.readNet(MODEL)

        # construct a blob from the image and then perform a forward pass of
        # the model to obtain the two output layer sets
        blob = cv2.dnn.blobFromImage(image, 1.0, (W, H),
                                     (123.68, 116.78, 103.94), swapRB=True, crop=False)
        start = time.time()
        self._net.setInput(blob)
        (scores, geometry) = self._net.forward(layerNames)
        end = time.time()

        # show timing information on text prediction
        print("[INFO] text detection took {:.6f} seconds".format(end - start))

        # grab the number of rows and columns from the scores volume, then
        # initialize our set of bounding box rectangles and corresponding
        # confidence scores
        (numRows, numCols) = scores.shape[2:4]
        rects = []
        confidences = []

        # loop over the number of rows
        for y in range(0, numRows):
            # extract the scores (probabilities), followed by the geometrical
            # data used to derive potential bounding box coordinates that
            # surround text
            scoresData = scores[0, 0, y]
            xData0 = geometry[0, 0, y]
            xData1 = geometry[0, 1, y]
            xData2 = geometry[0, 2, y]
            xData3 = geometry[0, 3, y]
            anglesData = geometry[0, 4, y]

            # loop over the number of columns
            for x in range(0, numCols):
                # if our score does not have sufficient probability, ignore it
                if scoresData[x] < MIN_CONFIDENCE:
                    continue

                # compute the offset factor as our resulting feature maps will
                # be 4x smaller than the input image
                (offsetX, offsetY) = (x * 4.0, y * 4.0)

                # extract the rotation angle for the prediction and then
                # compute the sin and cosine
                angle = anglesData[x]
                cos = np.cos(angle)
                sin = np.sin(angle)

                # use the geometry volume to derive the width and height of
                # the bounding box
                h = xData0[x] + xData2[x]
                w = xData1[x] + xData3[x]

                # compute both the starting and ending (x, y)-coordinates for
                # the text prediction bounding box
                endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
                endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
                startX = int(endX - w)
                startY = int(endY - h)

                # add the bounding box coordinates and probability score to
                # our respective lists
                rects.append((startX, startY, endX, endY))
                confidences.append(scoresData[x])

        # apply non-maxima suppression to suppress weak, overlapping bounding
        # boxes
        boxes = non_max_suppression(np.array(rects), probs=confidences)
        return len(boxes) > 0


SIGNS = [
    'Card',
    'Debit',
    'Credit',
    'Bank',
    'Signature',
    'Valid',
    'Unless',
    'Signed',
    'consular',
    'Class',
    'Exp',
    'CVV',
    'CV2',
    'SASS',
    'Licence',
    'Driver',
    'Visa',
    'MasterCard',
    'Password',
    'Established',
    'Permis',
    'Conduire',
    'Passport',
    'Pasaporte',
    'Federative',
    'Republic',
    'Prefecture'
]


def has_signature(text: str) -> bool:
    words = re.split(r'\W', text)
    for w in words:
        if len(w) > 0:
            for s in SIGNS:
                leven = fuzz.ratio(w.lower(), s.lower())
                if (leven > 90) or (len(s) > 4  and  leven > 75):
                    print(" ! Sign: {}, Word: {}, leven: {}".format(s, w, leven))
                    return True
    return False


def _resize(image):
    (H, W) = image.shape[:2]
    if max(H, W) <= 1536:
        return image

    if W > H:
        newW = min(1024, (W // 32) * 32)
        newH = round(newW * (H / W))
        newH = (newH // 32) * 32
    else:
        newH = min(1024, (H // 32) * 32)
        newW = round(newH * (W / H))
        newW = (newW // 32) * 32
    return cv2.resize(image, (newW, newH))


def check_image(path: str) -> bool:
    try:
        if not is_jpg(path):
            return False

        image = cv2.imread(path)
        image = _resize(image)
        for i in range(4):
            for psm in ['6', '3']:
                text = pytesseract.image_to_string(image, config='--psm ' + psm, lang='eng')
                #print("==================")
                #print("psm: {}, rotate: {}".format(psm, i*90))
                #print(text)
                if has_signature(text):
                    return True
            image = cv2.rotate(image, cv2.cv2.ROTATE_90_CLOCKWISE)
    except:
        logging.exception("Error checking image {}".format(path))

    return False


def detect_dir(directory):
    good_dir = os.path.join(directory, "good")
    other_dir = os.path.join(directory, "other")
    os.makedirs(good_dir, exist_ok=True)
    os.makedirs(other_dir, exist_ok=True)
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        if not os.path.isfile(f):
            continue
        print(filename)
        if check_image(f):
            shutil.copyfile(f, os.path.join(good_dir, filename))
        else:
            shutil.copyfile(f, os.path.join(other_dir, filename))


if __name__ == '__main__':
    #print(fuzz.ratio("ESTACLIGHED".lower(), "Established".lower()))
    #exit(0)
    # detect_dir("d:/gosms/interesting")
    has = check_image(r"d:\gosms\all\good\1252\12524776_autocompress1568993384219.jpg")
    print("=====")
    print(has)
