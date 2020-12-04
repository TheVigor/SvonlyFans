import face_recognition
import os
import shutil
import logging
import cv2


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
MEDIA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "all")
FACE_DIR = os.path.join(MEDIA_DIR, "face")


def detect_faces():
    if not os.path.exists(FACE_DIR):
        os.mkdir(FACE_DIR)

    for filename in os.listdir(MEDIA_DIR):
        if not (filename.endswith(".jpg") or filename.endswith(".img")):
            continue
        file = os.path.join(MEDIA_DIR, filename)
        try:
            image = face_recognition.load_image_file(file)
            face_locations = face_recognition.face_locations(image)
            if len(face_locations) == 0:
                continue
            shutil.copyfile(file, os.path.join(FACE_DIR, filename))
        except:
            logging.exception("Error occured trying to detect face in {}".format(filename))


if __name__ == '__main__':
    detect_faces()
