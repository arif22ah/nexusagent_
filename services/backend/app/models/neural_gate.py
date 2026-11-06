import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import tensorflow as tf
import torch
import torch.nn as nn


class PyTorchPolicyGate(nn.Module):
    def __init__(self, input_dim: int = 16):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 32),
            nn.ReLU(),
            nn.BatchNorm1d(32),
            nn.Dropout(0.1),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )
        self.eval()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        with torch.no_grad():
            return self.network(x)


class TensorFlowAuxiliaryValidator:
    def __init__(self):
        self.threshold = tf.constant(0.15, dtype=tf.float32)

    def compute_anomaly_metric(self, vector: np.ndarray) -> float:
        tensor = tf.convert_to_tensor(vector, dtype=tf.float32)
        return float(tf.math.reduce_variance(tensor).numpy())
