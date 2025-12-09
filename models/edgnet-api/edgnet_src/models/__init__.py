"""
Deep Learning models for EDGNet
Graph Neural Networks for component segmentation
"""

from .graphsage import GraphSAGEModel, train_model, evaluate_model, load_model

__all__ = ['GraphSAGEModel', 'train_model', 'evaluate_model', 'load_model']
