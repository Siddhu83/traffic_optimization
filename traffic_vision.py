import argparse
import json
import os
from datetime import datetime

import cv2
import numpy as np
from ultralytics import YOLO


def is_inside(point, polygon):
    """Return True if the point is inside the polygon using ray casting."""
    x, y = point
    inside = False

    for i in range(len(polygon)):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % len(polygon)]

        intersect = ((y1 > y) != (y2 > y)) and (
            x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1
        )
        if intersect:
            inside = not inside

    return inside


def build_lane_polygons(frame_width, frame_height):
    """Define the 4 lane polygon ROIs using normalized coordinates."""
    w, h = frame_width, frame_height
    return {
        "N": [
            (int(0.35 * w), int(0.05 * h)),
            (int(0.65 * w), int(0.05 * h)),
            (int(0.8 * w), int(0.4 * h)),
            (int(0.2 * w), int(0.4 * h)),
        ],
        "S": [
            (int(0.2 * w), int(0.6 * h)),
            (int(0.8 * w), int(0.6 * h)),
            (int(0.65 * w), int(0.95 * h)),
            (int(0.35 * w), int(0.95 * h)),
        ],
        "E": [
            (int(0.65 * w), int(0.2 * h)),
            (int(0.95 * w), int(0.2 * h)),
            (int(0.95 * w), int(0.8 * h)),
            (int(0.65 * w), int(0.8 * h)),
        ],
        "W": [
            (int(0.05 * w), int(0.2 * h)),
            (int(0.35 * w), int(0.2 * h)),
            (int(0.35 * w), int(0.8 * h)),
            (int(0.05 * w), int(0.8 * h)),
        ],
    }


def build_emergency_lane(frame_width, frame_height):
    """Define a dedicated emergency lane polygon."""
    w, h = frame_width, frame_height
    return [
        (int(0.75 * w), int(0.1 * h)),
        (int(0.95 * w), int(0.1 * h)),
        (int(0.95 * w), int(0.25 * h)),
        (int(0.75 * w), int(0.25 * h)),
    ]


def annotate_polygons(frame, lanes, emergency_lane):
    for lane_id, polygon in lanes.items():
        cv2.polylines(frame, [np.array(polygon, dtype=np.int32)], True, (0, 255, 0), 2)
        centroid = np.mean(np.array(polygon), axis=0).astype(int)
        cv2.putText(
            frame,
            lane_id,
            tuple(centroid),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )

    cv2.polylines(frame, [np.array(emergency_lane, dtype=np.int32)], True, (0, 165, 255), 2)
    cv2.putText(
        frame,
        "Emergency Lane",
        (emergency_lane[0][0], emergency_lane[0][1] - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 165, 255),
        2,
        cv2.LINE_AA,
    )


def main(video_source):
    model = YOLO("yolov8n.pt")
    target_classes = {"car", "bus", "truck"}

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video source: {video_source}")

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    lanes = build_lane_polygons(frame_width, frame_height)
    emergency_lane = build_emergency_lane(frame_width, frame_height)

    os.makedirs(os.path.dirname("traffic_state.json") or ".", exist_ok=True)
    frame_count = 0
    output_interval = 30
    skip_every = 2

    print("Starting traffic feed. Press ESC to exit.")

    while True:
        ret, frame = cap.read()
        frame_count += 1

        if not ret:
            print("Video ended or frame not available.")
            break

        if frame_count % skip_every != 0:
            if cv2.waitKey(1) == 27:
                break
            continue

        detection_frame = frame.copy()
        annotate_polygons(detection_frame, lanes, emergency_lane)

        counts = {"N": 0, "S": 0, "E": 0, "W": 0}
        emergency_detected = False

        results = model(frame)[0]
        for box, cls_idx, score in zip(results.boxes.xyxy, results.boxes.cls, results.boxes.conf):
            class_name = model.names[int(cls_idx)]
            if class_name not in target_classes:
                continue

            x1, y1, x2, y2 = map(int, box.tolist())
            bottom_center = ((x1 + x2) // 2, y2)
            assigned_lane = None

            for lane_id, polygon in lanes.items():
                if is_inside(bottom_center, polygon):
                    counts[lane_id] += 1
                    assigned_lane = lane_id
                    break

            priority_vehicle = class_name in {"bus", "truck"}
            emergency_lane_hit = is_inside(bottom_center, emergency_lane)
            if priority_vehicle or emergency_lane_hit:
                emergency_detected = True

            label = f"{class_name} {score:.2f}"
            if priority_vehicle:
                label += " (PRIORITY)"

            cv2.rectangle(detection_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            cv2.circle(detection_frame, bottom_center, 4, (0, 0, 255), -1)
            cv2.putText(
                detection_frame,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )
            if assigned_lane:
                cv2.putText(
                    detection_frame,
                    assigned_lane,
                    (bottom_center[0] + 5, bottom_center[1] - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2,
                    cv2.LINE_AA,
                )

        if frame_count % output_interval == 0:
            timestamp = datetime.utcnow().isoformat() + "Z"
            state = {
                "lanes": counts,
                "emergency": emergency_detected,
                "timestamp": timestamp,
            }
            output = json.dumps(state)
            print(output)
            with open("traffic_state.json", "a", encoding="utf-8") as fp:
                fp.write(output + "\n")

        cv2.imshow("Traffic Vision", detection_frame)
        if cv2.waitKey(1) == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Traffic vision stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real-time traffic lane counting with YOLOv8")
    parser.add_argument(
        "--source",
        default=0,
        help="Video source: device index or file path (default=0)",
    )
    args = parser.parse_args()

    try:
        main(args.source)
    except Exception as exc:
        print(f"Error: {exc}")
