"""
GraphSAGE model for component classification
Based on Hamilton et al., NeurIPS 2017
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
from torch_geometric.data import Data
import numpy as np
from tqdm import tqdm


class GraphSAGEModel(nn.Module):
    """
    GraphSAGE model for node classification

    Architecture:
    - 2 SAGEConv layers with ReLU activation
    - Dropout for regularization
    - Final linear layer for classification
    """

    def __init__(self, in_channels, hidden_channels, out_channels, dropout=0.5, num_layers=2):
        """
        Args:
            in_channels: Input feature dimension (19 for EDGNet)
            hidden_channels: Hidden layer dimension
            out_channels: Number of classes (2 or 3 or 4)
            dropout: Dropout probability
            num_layers: Number of GraphSAGE conv layers (default 2)
        """
        super(GraphSAGEModel, self).__init__()

        # Use ModuleList - last layer outputs to num_classes
        self.convs = nn.ModuleList()
        self.convs.append(SAGEConv(in_channels, hidden_channels))
        # Last conv layer goes from hidden to output classes
        self.convs.append(SAGEConv(hidden_channels, out_channels))
        
        self.dropout = dropout
        self.num_layers = num_layers
    def forward(self, x, edge_index):
        """
        Forward pass

        Args:
            x: Node features (num_nodes, in_channels)
            edge_index: Graph edges (2, num_edges)

        Returns:
            Log probabilities for each class
        """
        # Apply all conv layers
        for i, conv in enumerate(self.convs):
            x = conv(x, edge_index)
            # Apply ReLU and dropout except on last layer
            if i < len(self.convs) - 1:
                x = F.relu(x)
                x = F.dropout(x, p=self.dropout, training=self.training)
        
        return F.log_softmax(x, dim=1)
    def predict(self, x, edge_index):
        """
        Predict class labels

        Args:
            x: Node features
            edge_index: Edge indices

        Returns:
            Predicted class indices
        """
        self.eval()
        with torch.no_grad():
            logits = self.forward(x, edge_index)
            predictions = torch.argmax(logits, dim=1)
        return predictions


def create_data_object(node_features, edge_index, labels=None, train_mask=None, val_mask=None, test_mask=None):
    """
    Create PyTorch Geometric Data object

    Args:
        node_features: Node feature matrix (num_nodes, feature_dim)
        edge_index: Edge index tensor (2, num_edges)
        labels: Ground truth labels (num_nodes,)
        train_mask: Boolean mask for training nodes
        val_mask: Boolean mask for validation nodes
        test_mask: Boolean mask for test nodes

    Returns:
        Data object
    """
    data = Data(
        x=torch.tensor(node_features, dtype=torch.float),
        edge_index=torch.tensor(edge_index, dtype=torch.long)
    )

    if labels is not None:
        data.y = torch.tensor(labels, dtype=torch.long)

    if train_mask is not None:
        data.train_mask = torch.tensor(train_mask, dtype=torch.bool)

    if val_mask is not None:
        data.val_mask = torch.tensor(val_mask, dtype=torch.bool)

    if test_mask is not None:
        data.test_mask = torch.tensor(test_mask, dtype=torch.bool)

    return data


def train_model(model, data, num_epochs=200, learning_rate=0.01, weight_decay=5e-4, device='cpu'):
    """
    Train GraphSAGE model

    Args:
        model: GraphSAGE model
        data: PyTorch Geometric Data object with train/val masks
        num_epochs: Number of training epochs
        learning_rate: Learning rate
        weight_decay: L2 regularization
        device: 'cpu' or 'cuda'

    Returns:
        Dictionary with training history
    """
    model = model.to(device)
    data = data.to(device)

    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)
    criterion = nn.CrossEntropyLoss()

    history = {
        'train_loss': [],
        'train_acc': [],
        'val_loss': [],
        'val_acc': []
    }

    best_val_acc = 0
    best_model_state = None

    for epoch in tqdm(range(num_epochs), desc='Training'):
        # Training
        model.train()
        optimizer.zero_grad()

        out = model(data.x, data.edge_index)
        loss = criterion(out[data.train_mask], data.y[data.train_mask])

        loss.backward()
        optimizer.step()

        # Calculate training accuracy
        with torch.no_grad():
            pred = torch.argmax(out[data.train_mask], dim=1)
            train_acc = (pred == data.y[data.train_mask]).float().mean().item()

        history['train_loss'].append(loss.item())
        history['train_acc'].append(train_acc)

        # Validation
        if hasattr(data, 'val_mask'):
            model.eval()
            with torch.no_grad():
                out = model(data.x, data.edge_index)
                val_loss = criterion(out[data.val_mask], data.y[data.val_mask]).item()
                pred = torch.argmax(out[data.val_mask], dim=1)
                val_acc = (pred == data.y[data.val_mask]).float().mean().item()

            history['val_loss'].append(val_loss)
            history['val_acc'].append(val_acc)

            # Save best model
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                best_model_state = model.state_dict().copy()

            if (epoch + 1) % 20 == 0:
                print(f'Epoch {epoch+1}/{num_epochs}: '
                      f'Train Loss: {loss.item():.4f}, Train Acc: {train_acc:.4f}, '
                      f'Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.4f}')

    # Load best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
        print(f'\nBest validation accuracy: {best_val_acc:.4f}')

    return history


def evaluate_model(model, data, device='cpu'):
    """
    Evaluate model on test set

    Args:
        model: Trained GraphSAGE model
        data: Data object with test_mask
        device: 'cpu' or 'cuda'

    Returns:
        Dictionary with test metrics
    """
    model = model.to(device)
    data = data.to(device)
    model.eval()

    with torch.no_grad():
        out = model(data.x, data.edge_index)
        pred = torch.argmax(out[data.test_mask], dim=1)
        correct = (pred == data.y[data.test_mask]).float()
        accuracy = correct.mean().item()

        # Per-class accuracy
        num_classes = out.size(1)
        per_class_acc = []

        for c in range(num_classes):
            mask = (data.y[data.test_mask] == c)
            if mask.sum() > 0:
                class_acc = correct[mask].mean().item()
                per_class_acc.append(class_acc)
            else:
                per_class_acc.append(0.0)

    metrics = {
        'accuracy': accuracy,
        'per_class_accuracy': per_class_acc,
        'predictions': pred.cpu().numpy(),
        'labels': data.y[data.test_mask].cpu().numpy()
    }

    print(f"\nTest Results:")
    print(f"  Overall Accuracy: {accuracy:.4f}")
    for i, acc in enumerate(per_class_acc):
        print(f"  Class {i} Accuracy: {acc:.4f}")

    return metrics


def save_model(model, path):
    """Save model checkpoint"""
    torch.save({
        'model_state_dict': model.state_dict(),
        'model_config': {
            'in_channels': model.conv1.in_channels,
            'hidden_channels': model.conv1.out_channels,
            'out_channels': model.fc.out_features,
            'dropout': model.dropout
        }
    }, path)
    print(f"Model saved to {path}")


def load_model(path, device='cpu'):
    """Load model checkpoint"""
    checkpoint = torch.load(path, map_location=device)
    config = checkpoint['model_config']

    model = GraphSAGEModel(
        in_channels=config['in_channels'],
        hidden_channels=config['hidden_channels'],
        out_channels=config['out_channels'],
        dropout=config.get('dropout', 0.5)  # Default to 0.5 if not in config
    )
    model.load_state_dict(checkpoint['model_state_dict'])
    model = model.to(device)

    print(f"Model loaded from {path}")
    return model


if __name__ == '__main__':
    # Test GraphSAGE model with synthetic data
    print("Testing GraphSAGE model...")

    # Create synthetic graph data
    num_nodes = 100
    num_features = 19
    num_classes = 3

    # Random features
    x = torch.randn(num_nodes, num_features)

    # Random edges
    num_edges = 200
    edge_index = torch.randint(0, num_nodes, (2, num_edges))

    # Random labels
    y = torch.randint(0, num_classes, (num_nodes,))

    # Train/val/test split
    train_mask = torch.zeros(num_nodes, dtype=torch.bool)
    train_mask[:60] = True

    val_mask = torch.zeros(num_nodes, dtype=torch.bool)
    val_mask[60:80] = True

    test_mask = torch.zeros(num_nodes, dtype=torch.bool)
    test_mask[80:] = True

    # Create data object
    data = Data(x=x, edge_index=edge_index, y=y,
                train_mask=train_mask, val_mask=val_mask, test_mask=test_mask)

    # Create model
    model = GraphSAGEModel(in_channels=num_features, hidden_channels=64,
                           out_channels=num_classes, dropout=0.5)

    print(f"Model architecture:")
    print(model)

    # Train model
    print("\nTraining model...")
    history = train_model(model, data, num_epochs=50, learning_rate=0.01)

    # Evaluate model
    print("\nEvaluating model...")
    metrics = evaluate_model(model, data)

    print("\nTest completed successfully!")
