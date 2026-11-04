
from pathlib import Path
import json
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

PROJECT_DIR = Path(__file__).resolve().parent.parent

# Original PlantVillage image folders
DATASET_DIR = Path(
    r"D:\files\PlantVillage-Dataset-master"
    r"\PlantVillage-Dataset-master\raw\color"
)

MODEL_DIR = PROJECT_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_SIZE = (128, 128)
BATCH_SIZE = 32
EPOCHS = 15
SEED = 42

print("TensorFlow:", tf.__version__)
print("Dataset:", DATASET_DIR)

if not DATASET_DIR.is_dir():
    raise FileNotFoundError(f"Dataset not found: {DATASET_DIR}")

# Create training and validation datasets
train_ds = keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="training",
    seed=SEED,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="int",
)

val_ds = keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="validation",
    seed=SEED,
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="int",
)

class_names = train_ds.class_names
num_classes = len(class_names)

if num_classes < 2:
    raise ValueError("At least two image classes are required.")

print(f"Found {num_classes} classes:")
for index, name in enumerate(class_names):
    print(f"{index}: {name}")

(MODEL_DIR / "class_labels.txt").write_text(
    "\n".join(class_names) + "\n",
    encoding="utf-8",
)

AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.prefetch(AUTOTUNE)
val_ds = val_ds.prefetch(AUTOTUNE)

model = keras.Sequential([
    layers.Input(shape=(128, 128, 3)),
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.08),
    layers.Rescaling(1.0 / 255),

    layers.Conv2D(32, 3, padding="same", activation="relu"),
    layers.MaxPooling2D(),

    layers.Conv2D(64, 3, padding="same", activation="relu"),
    layers.MaxPooling2D(),

    layers.Conv2D(128, 3, padding="same", activation="relu"),
    layers.MaxPooling2D(),

    layers.GlobalAveragePooling2D(),
    layers.Dropout(0.3),
    layers.Dense(128, activation="relu"),
    layers.Dense(num_classes, activation="softmax"),
])

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

model.summary()

best_model = MODEL_DIR / "crop_disease_model.keras"

callbacks = [
    keras.callbacks.ModelCheckpoint(
        str(best_model),
        monitor="val_accuracy",
        save_best_only=True,
        mode="max",
        verbose=1,
    ),
    keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=3,
        restore_best_weights=True,
        verbose=1,
    ),
]

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    callbacks=callbacks,
)

# Save the final model in both formats.
model.save(MODEL_DIR / "crop_disease_model.keras")
model.save(MODEL_DIR / "crop_disease_model.h5")

(MODEL_DIR / "training_history.json").write_text(
    json.dumps(
        {
            key: [float(value) for value in values]
            for key, values in history.history.items()
        },
        indent=2,
    ),
    encoding="utf-8",
)

print("\nTraining completed successfully.")
print("Model:", MODEL_DIR / "crop_disease_model.h5")
print("Labels:", MODEL_DIR / "class_labels.txt")
