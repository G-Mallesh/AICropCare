import os
import numpy as np
from PIL import Image
from tensorflow.keras.models import load_model

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(
    BASE_DIR, "models", "crop_disease_model.h5"
)

LABELS_PATH = os.path.join(
    BASE_DIR, "models", "class_labels.txt"
)

_model = None
_labels = None


def load_crop_model():
    global _model, _labels

    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Trained crop disease model is missing: {MODEL_PATH}"
            )

        if not os.path.exists(LABELS_PATH):
            raise FileNotFoundError(
                f"Model class labels file is missing: {LABELS_PATH}"
            )

        _model = load_model(MODEL_PATH)

        with open(LABELS_PATH, "r", encoding="utf-8") as file:
            _labels = [
                line.strip()
                for line in file
                if line.strip()
            ]

        if not _labels:
            raise ValueError("The class labels file is empty.")

    return _model, _labels


def predict_disease(image_path):
    model, labels = load_crop_model()

    if not os.path.isfile(image_path):
        raise FileNotFoundError(
            f"Uploaded image not found: {image_path}"
        )

    # Read and preprocess image
    with Image.open(image_path) as original_image:
        image = original_image.convert("RGB")
        image = image.resize((224, 224))

        image_array = np.array(
            image,
            dtype=np.float32
        )

    image_array = image_array / 255.0
    image_array = np.expand_dims(image_array, axis=0)

    # Run model prediction
    predictions = model.predict(
        image_array,
        verbose=0
    )[0]

    if len(predictions) != len(labels):
        raise ValueError(
            f"Model output classes ({len(predictions)}) "
            f"do not match label count ({len(labels)})."
        )

    predicted_index = int(np.argmax(predictions))

    disease_name = labels[predicted_index]

    confidence = float(predictions[predicted_index]) * 100

    return disease_name, round(confidence, 2)
