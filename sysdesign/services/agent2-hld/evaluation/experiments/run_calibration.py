"""
Research Experiment — Threshold Calibration Runner

Sweeps semantic similarity thresholds θ_rts (0.30 to 0.80) and θ_qac (0.30 to 0.80)
against manually labelled ground-truth requirements-component datasets.
Identifies the optimal F1-score threshold and prints full Precision/Recall/F1 tables.
"""

import sys
import json
import io
import logging
from pathlib import Path

# Reconfigure stdout for Windows console unicode support
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

from evaluation.calibration import calibrate_rts_threshold, calibrate_qac_threshold
from evaluation.rts import compute_rts
from evaluation.qac import compute_qac

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("Calibration-Runner")


def run_calibration_experiment(sample_file: str | None = None):
    """Run calibration experiment for RTS and QAC thresholds."""
    if not sample_file:
        sample_file = str(BASE_DIR / "input" / "sample_food_delivery.json")

    with open(sample_file, "r", encoding="utf-8") as f:
        requirements = json.load(f)

    # Synthetic ground truth for sample_food_delivery.json
    # In full benchmark, this is loaded from human expert annotations
    gt_rts = {
        "FR-1": ["OrderApiGateway", "OrderService", "OrderRepository"],
        "FR-2": ["OrderService"],
        "FR-3": ["PaymentGatewayService", "PaymentRepository"],
        "FR-4": ["DeliveryService", "DeliveryRepository"],
        "FR-5": ["NotificationHandler"],
    }

    gt_qac = {
        "NFR-1": ["OrderService", "OrderApiGateway"],
        "NFR-2": ["PaymentGatewayService"],
        "NFR-3": ["DeliveryService"],
        "NFR-4": ["OrderRepository", "PaymentRepository", "DeliveryRepository"],
    }

    mock_arch = {
        "architecture_style": "Layered Architecture",
        "layers": [
            {"name": "Presentation Layer", "order": 1},
            {"name": "Application Layer", "order": 2},
            {"name": "Data Access Layer", "order": 3},
        ],
        "components": [
            {"name": "OrderApiGateway", "layer": "Presentation Layer", "responsibilities": ["API gateway request routing", "Authentication and rate limiting"]},
            {"name": "OrderService", "layer": "Application Layer", "responsibilities": ["Order lifecycle management", "Status tracking and orchestration"]},
            {"name": "PaymentGatewayService", "layer": "Application Layer", "responsibilities": ["Payment processing integration", "Secure transaction handling"]},
            {"name": "DeliveryService", "layer": "Application Layer", "responsibilities": ["Driver assignment proximity dispatch", "Realtime delivery location tracking"]},
            {"name": "NotificationHandler", "layer": "Application Layer", "responsibilities": ["Push notifications dispatches", "Customer SMS receipts"]},
            {"name": "OrderRepository", "layer": "Data Access Layer", "responsibilities": ["Persist order data", "Transactional database queries"]},
            {"name": "PaymentRepository", "layer": "Data Access Layer", "responsibilities": ["Payment history ledger data", "Audit logging store"]},
            {"name": "DeliveryRepository", "layer": "Data Access Layer", "responsibilities": ["GPS tracking history persistence", "Driver route store"]},
        ],
        "connectors": [
            {"from_component": "OrderApiGateway", "to_component": "OrderService", "connector_type": "sync_call"},
            {"from_component": "OrderService", "to_component": "OrderRepository", "connector_type": "sync_call"},
            {"from_component": "OrderService", "to_component": "PaymentGatewayService", "connector_type": "sync_call"},
            {"from_component": "PaymentGatewayService", "to_component": "PaymentRepository", "connector_type": "sync_call"},
            {"from_component": "OrderService", "to_component": "DeliveryService", "connector_type": "sync_call"},
            {"from_component": "DeliveryService", "to_component": "DeliveryRepository", "connector_type": "sync_call"},
        ]
    }

    print("\n=======================================================")
    print("      RESEARCH EXPERIMENT: THRESHOLD CALIBRATION       ")
    print("=======================================================\n")

    # RTS Calibration
    rts_res = calibrate_rts_threshold(gt_rts, mock_arch, requirements)
    print("--- RTS (Requirement Traceability Score) Threshold Sweep ---")
    print("| Threshold θ_rts | Precision | Recall | F1 Score | TP | FP | FN |")
    print("|-----------------|-----------|--------|----------|----|----|----|")
    for row in rts_res["sweep"]:
        star = " ★ (Best)" if row["threshold"] == rts_res["best_threshold"] else ""
        print(f"| {row['threshold']:15.2f} | {row['precision']:9.4f} | {row['recall']:6.4f} | {row['f1']:8.4f} | {row['tp']:2d} | {row['fp']:2d} | {row['fn']:2d} |{star}")

    print(f"\nOptimal RTS Threshold: θ_rts = {rts_res['best_threshold']} (Max F1 = {rts_res['best_f1']:.4f})")

    # QAC Calibration
    qac_res = calibrate_qac_threshold(gt_qac, mock_arch, requirements)
    print("\n--- QAC (Quality Attribute Coverage) Threshold Sweep ---")
    print("| Threshold θ_qac | Precision | Recall | F1 Score | TP | FP | FN |")
    print("|-----------------|-----------|--------|----------|----|----|----|")
    for row in qac_res["sweep"]:
        star = " ★ (Best)" if row["threshold"] == qac_res["best_threshold"] else ""
        print(f"| {row['threshold']:15.2f} | {row['precision']:9.4f} | {row['recall']:6.4f} | {row['f1']:8.4f} | {row['tp']:2d} | {row['fp']:2d} | {row['fn']:2d} |{star}")

    print(f"\nOptimal QAC Threshold: θ_qac = {qac_res['best_threshold']} (Max F1 = {qac_res['best_f1']:.4f})\n")

    return {
        "rts_optimal": rts_res["best_threshold"],
        "qac_optimal": qac_res["best_threshold"],
        "rts_calibration": rts_res,
        "qac_calibration": qac_res,
    }


if __name__ == "__main__":
    run_calibration_experiment()
