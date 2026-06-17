"""
Train the floor-detection model.

This is the cleaned-up script version of the notebook I used on Kaggle. It takes
the Roboflow export, fixes the labels (some floors were drawn as polygons, YOLO
detection wants boxes), and trains YOLOv11-L on it.

Run on a machine with a GPU. On Kaggle I used two T4s.
"""

from pathlib import Path
import shutil
import yaml
from ultralytics import YOLO

# Where the Roboflow export landed, and where to put the fixed copy.
DATASET = Path("/kaggle/input/datasets/muhammadwajihhyder/fyp2floorv2/FYP2Floor.v1i.yolov11")
FIXED = Path("/kaggle/working/dataset")
DATA_YAML = Path("/kaggle/working/data.yaml")

IMG_SIZE = 960
EPOCHS = 150
SEED = 42


def polygon_to_box(parts):
    """A polygon label is 'cls x1 y1 x2 y2 ...'. Turn it into a YOLO box."""
    cls = parts[0]
    coords = list(map(float, parts[1:]))
    xs, ys = coords[0::2], coords[1::2]
    cx = (min(xs) + max(xs)) / 2
    cy = (min(ys) + max(ys)) / 2
    w = max(xs) - min(xs)
    h = max(ys) - min(ys)
    return f"{cls} {cx} {cy} {w} {h}"


def fix_labels():
    """Copy images across and rewrite any polygon labels as boxes."""
    if FIXED.exists():
        shutil.rmtree(FIXED)

    boxes, polys = 0, 0
    for split in ("train", "valid", "test"):
        img_out = FIXED / split / "images"
        lbl_out = FIXED / split / "labels"
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)

        # symlink the images instead of copying, the dataset is large
        for img in (DATASET / split / "images").iterdir():
            (img_out / img.name).symlink_to(img)

        for lbl in (DATASET / split / "labels").glob("*.txt"):
            lines = []
            for line in lbl.read_text().strip().splitlines():
                parts = line.split()
                if len(parts) == 5:          # already a box
                    lines.append(line)
                    boxes += 1
                elif len(parts) >= 7:        # polygon -> box
                    lines.append(polygon_to_box(parts))
                    polys += 1
            (lbl_out / lbl.name).write_text("\n".join(lines) + "\n")

    print(f"kept {boxes} boxes, converted {polys} polygons")


def write_data_yaml():
    """Roboflow's data.yaml has relative paths. Repoint it at the fixed dataset."""
    cfg = yaml.safe_load((DATASET / "data.yaml").read_text())
    cfg["path"] = str(FIXED)
    cfg["train"] = "train/images"
    cfg["val"] = "valid/images"
    cfg["test"] = "test/images"
    DATA_YAML.write_text(yaml.safe_dump(cfg))


def train():
    # yolo11l was the sweet spot: better than m, and x kept running out of
    # memory at 960 and overfitting on ~1k images.
    model = YOLO("yolo11l.pt")
    model.train(
        data=str(DATA_YAML),
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=16,               # 8 per GPU across the two T4s
        patience=30,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        cos_lr=True,
        weight_decay=0.0005,
        warmup_epochs=3,
        close_mosaic=15,        # last 15 epochs without mosaic, cleaner finish
        mosaic=1.0,
        mixup=0.10,
        hsv_h=0.015, hsv_s=0.7, hsv_v=0.4,
        degrees=10, translate=0.1, scale=0.5, fliplr=0.5,
        device=[0, 1],
        workers=8,
        seed=SEED,
        name="floor_yolo11l_det",
    )
    return model


def main():
    fix_labels()
    write_data_yaml()
    model = train()

    # Evaluate at the same image size used for training, otherwise the numbers drop.
    metrics = model.val(data=str(DATA_YAML), split="test", imgsz=IMG_SIZE, conf=0.001, iou=0.6)
    print("mAP@0.5   :", metrics.box.map50)
    print("mAP@0.5-95:", metrics.box.map)
    print("best weights are under runs/detect/floor_yolo11l_det/weights/best.pt")


if __name__ == "__main__":
    main()
