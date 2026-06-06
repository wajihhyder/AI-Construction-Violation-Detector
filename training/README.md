# Floor-Detection Model — Training & Evaluation

This directory contains the machine-learning pipeline behind the AI screening layer of the
**AI-Powered Construction Violation Detection** system: a **YOLOv11** object-detection model that
locates and counts the floors of a building from a street-view photograph. The floor count is then
compared against per-district SBCA limits by the backend rule engine to flag potential violations.

> **Author of this component:** Muhammad Wajih Hyder — data collection & curation, annotation,
> model training, evaluation, and integration.

- 📓 Notebook: [`floor_detection_yolov11.ipynb`](floor_detection_yolov11.ipynb)
- 🏋️ Trained weights: [`../best_floor.pt`](../best_floor.pt)
- 🔌 Inference integration: [`../backend/services/ai_service.py`](../backend/services/ai_service.py)

---

## 1. Problem framing

Given a street-view image of a building, **detect each floor** as an object. The number of detected
floors is the signal the rule engine uses to decide compliance (e.g. *"6 floors detected; max
allowed in this district is 4 → Extra_Floor violation"*).

This is framed as **single-class object detection** (`floor`) rather than instance segmentation —
see [§3](#3-why-detection-not-segmentation) for the reasoning.

---

## 2. Dataset

| Stage | Count |
| :--- | :--- |
| Images collected from various sources | **4,500** |
| Images kept after manual usability screening & annotated in **Roboflow** | **1,090** |
| Total annotated floor instances | **4,015** |

**Splits** (Roboflow project `fyp2floor`, exported in YOLOv11 format, licensed CC BY 4.0):

| Split | Images | Floor instances | Median image size | Median instances/img |
| :--- | :---: | :---: | :---: | :---: |
| train | 872 | 3,254 | 1031 × 683 | 3 |
| valid | 109 | 395 | 1076 × 644 | 3 |
| test | 109 | 366 | 1104 × 710 | 3 |

Annotation guidelines: one box per visible storey on the primary façade; a single `floor` class.
Images span varied building types, lighting, and viewing angles to improve generalisation.

---

## 3. Why detection, not segmentation

Roboflow's *Instance Segmentation* export turned out to be **~98% axis-aligned rectangles**
(3,918 bounding boxes vs. only 97 true polygons). Training a segmentation head on what are
effectively rectangular masks caps `mAP50-95` artificially — both the predicted and ground-truth
"masks" are rectangles, so the box metric is the only meaningful one anyway.

The pipeline therefore **normalises every label to a bounding box** before training: polygon labels
are collapsed to their axis-aligned bounding box (AABB), and existing boxes are kept as-is. Images
are symlinked (not copied) into the working dataset; only the label files are rewritten.

```
Kept 3918 bbox labels as-is
Converted 97 polygon labels -> AABB bbox
```

---

## 4. Pre-flight checks (predicting the ceiling before a long run)

Two cheap steps run **before** the full training job to avoid wasting GPU hours:

**a) Data audit** — checks min samples per class, class imbalance, train/val distribution shift,
unlabeled (background) images, suspiciously tiny boxes (likely mislabels), and total dataset size.
The dataset passed with **0 FAIL / 0 WARN**.

**b) Smoke test** — trains the smallest model (`yolo11n`, 15 epochs) as a fast predictor of the
achievable ceiling. For this kind of task, a tiny model already in striking distance strongly
implies a larger model trained longer will reach the target — which proved correct.

---

## 5. Training configuration

Final model: **`yolo11l`** — the best detection accuracy that fits comfortably on 2× T4 at
`imgsz=960`. `yolo11x` was rejected for OOM risk and overfitting tendency on a ~1k-image dataset.

```python
from ultralytics import YOLO

model = YOLO("yolo11l.pt")
model.train(
    data="data.yaml",
    task="detect",
    epochs=150,
    imgsz=960,
    batch=16,              # 8 per GPU across 2× T4
    patience=30,
    optimizer="AdamW",
    lr0=0.001, lrf=0.01, cos_lr=True,
    weight_decay=0.0005, warmup_epochs=3,
    close_mosaic=15,       # disable mosaic for the last 15 epochs
    mosaic=1.0, mixup=0.10,
    hsv_h=0.015, hsv_s=0.7, hsv_v=0.4,
    degrees=10, translate=0.1, scale=0.5, fliplr=0.5,
    device=[0, 1], workers=8, seed=42,
)
```

**Environment:** Kaggle, 2× NVIDIA Tesla T4, Ultralytics 8.x, PyTorch 2.x (CUDA).

---

## 6. Results

Evaluated on the **held-out test split** at `imgsz=960` (matching training resolution):

| Metric | Score |
| :--- | :---: |
| **mAP@50** | **0.933** |
| mAP@50–95 | 0.629 |
| Precision | 0.906 |
| Recall | 0.897 |

A per-image diagnostic (ground-truth count vs. predictions at `conf=0.001` with max confidence) is
included in the notebook to distinguish genuine model failures from labelling issues and
out-of-distribution images.

<!-- Add a grid of annotated predictions. Suggested file: ../docs/screenshots/model_predictions.png -->
![Sample floor detections](../docs/screenshots/model_predictions.png)

---

## 7. How the backend uses the model

At inference time, [`backend/services/ai_service.py`](../backend/services/ai_service.py):

1. Lazily loads `best_floor.pt` via Ultralytics `YOLO` (cached across requests).
2. Runs `model.predict(...)` on the uploaded street-view image
   (`conf=0.15`, `iou=0.3` by default — tuned for the stacked-floor case).
3. Counts the detected `floor` boxes.
4. Passes the count to the **SBCA rule engine** ([`rule_engine.py`](../backend/services/rule_engine.py)),
   which flags an `Extra_Floor` violation when the count exceeds the district's maximum.
5. Saves an **annotated evidence image** for the authority dashboard.

Inference thresholds are configurable via environment variables
(`AI_STREET_MODEL_CONFIDENCE`, `AI_STREET_MODEL_IOU`, `AI_DEVICE`).

---

## 8. Reproducing the training

1. Open [`floor_detection_yolov11.ipynb`](floor_detection_yolov11.ipynb) on Kaggle
   (Settings → Accelerator → **GPU T4 ×2**).
2. Attach the floor dataset and update `DATASET_PATH` to match its slug.
3. Run the cells top to bottom: label normalisation → audit → smoke test → full training → evaluation.
4. The best checkpoint is written to `runs/floor_yolo11l_det/weights/best.pt` — this is the file
   shipped as `best_floor.pt`.

> Optional: export to ONNX for deployment with `YOLO(best).export(format="onnx", imgsz=960)`.

---

## 9. Future work

- A dedicated **aerial model** for setback / encroachment detection (street-view model detects floors only).
- Dataset expansion across more districts and conditions, plus targeted hard-negative mining.
- Quantisation / ONNX-TensorRT export for faster CPU and edge inference.
