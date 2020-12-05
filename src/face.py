import face_recognition
import os
import shutil
import logging
from PIL import Image, ImageDraw


def is_image(path: str) -> bool:
    with open(path, "rb") as f:
        buf = f.read(4)
    for sign in ['ffd8']:  # , '89504e47']:
        if buf.startswith(bytearray.fromhex(sign)):
            return True
    return False


def detect_face(media_dir: str, face_dir: str, sub_path: str) -> bool:
    try:
        path = os.path.join(media_dir, sub_path)
        if not is_image(path):
            return False
        image = face_recognition.load_image_file(path)
        face_locations = face_recognition.face_locations(image)
        if (face_locations is None) or (len(face_locations) == 0):
            return False

        to = os.path.join(face_dir, sub_path)
        os.makedirs(os.path.dirname(to), exist_ok=True)
        shutil.copyfile(path, to)
        return True
    except:
        logging.exception("Error occured trying to detect face in {}".format(sub_path))
        return False


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
# MEDIA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "all")
MEDIA_DIR = "d:\\gosms\\all"
FACE_DIR = os.path.join(MEDIA_DIR, "face")


def draw_faces(path: str):
    if not is_image(path):
        print("{} is not a JPEG image".format(path))
        return False
    image = face_recognition.load_image_file(path)
    # Find all facial features in all the faces in the image
    face_landmarks_list = face_recognition.face_landmarks(image)

    pil_image = Image.fromarray(image)
    for face_landmarks in face_landmarks_list:
        d = ImageDraw.Draw(pil_image, 'RGBA')

        # Make the eyebrows into a nightmare
        d.polygon(face_landmarks['left_eyebrow'], fill=(68, 54, 39, 128))
        d.polygon(face_landmarks['right_eyebrow'], fill=(68, 54, 39, 128))
        d.line(face_landmarks['left_eyebrow'], fill=(68, 54, 39, 150), width=5)
        d.line(face_landmarks['right_eyebrow'], fill=(68, 54, 39, 150), width=5)

        # Gloss the lips
        d.polygon(face_landmarks['top_lip'], fill=(150, 0, 0, 128))
        d.polygon(face_landmarks['bottom_lip'], fill=(150, 0, 0, 128))
        d.line(face_landmarks['top_lip'], fill=(150, 0, 0, 64), width=8)
        d.line(face_landmarks['bottom_lip'], fill=(150, 0, 0, 64), width=8)

        # Sparkle the eyes
        d.polygon(face_landmarks['left_eye'], fill=(255, 255, 255, 30))
        d.polygon(face_landmarks['right_eye'], fill=(255, 255, 255, 30))

        # Apply some eyeliner
        d.line(face_landmarks['left_eye'] + [face_landmarks['left_eye'][0]], fill=(0, 0, 0, 110), width=6)
        d.line(face_landmarks['right_eye'] + [face_landmarks['right_eye'][0]], fill=(0, 0, 0, 110), width=6)

        # pil_image.show()
        with open(path + "_.jpg", "wb") as f:
            pil_image.save(f)


if __name__ == '__main__':
    draw_faces("c:\\Projects\\gosms\\SvonlyFans\\154689_autocompress1504217908538.jpg")
