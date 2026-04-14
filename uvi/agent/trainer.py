"""
Federated Trainer – Local training with gradient proof submission
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
import hashlib
import time
from dataclasses import dataclass
from typing import Tuple

@dataclass
class TrainingStats:
    """Statistics from a training round"""
    epoch: int
    batch: int
    loss: float
    accuracy: float
    gradient_hash: str
    submission_time: float

class SimpleModel(nn.Module):
    """Simple CNN for MNIST"""
    
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, 3, padding=1)
        self.fc1 = nn.Linear(64 * 7 * 7, 128)
        self.fc2 = nn.Linear(128, 10)
        self.pool = nn.MaxPool2d(2)
        
    def forward(self, x):
        x = self.pool(torch.relu(self.conv1(x)))
        x = self.pool(torch.relu(self.conv2(x)))
        x = x.view(x.size(0), -1)
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x

class FederatedTrainer:
    """
    Trains a model locally and submits gradient proofs for aggregation
    """
    
    def __init__(self, device_id: str, model_version: int = 1):
        self.device_id = device_id
        self.model_version = model_version
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Model setup
        self.model = SimpleModel().to(self.device)
        self.optimizer = optim.SGD(self.model.parameters(), lr=0.01, momentum=0.9)
        self.criterion = nn.CrossEntropyLoss()
        
        # Data
        self.train_loader = self._init_dataset()
        self.test_loader = self._init_test_dataset()
        
        # History
        self.stats_history = []
        
    def _init_dataset(self) -> DataLoader:
        """Load MNIST training data"""
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,))
        ])
        
        dataset = datasets.MNIST(
            root='./.data',
            train=True,
            download=True,
            transform=transform
        )
        
        return DataLoader(dataset, batch_size=32, shuffle=True)
    
    def _init_test_dataset(self) -> DataLoader:
        """Load MNIST test data"""
        transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,))
        ])
        
        dataset = datasets.MNIST(
            root='./.data',
            train=False,
            download=True,
            transform=transform
        )
        
        return DataLoader(dataset, batch_size=32, shuffle=False)
    
    def hash_gradients(self) -> str:
        """
        Compute deterministic SHA256 hash of all gradient values
        This is what gets proven in the ZK circuit
        """
        grad_bytes = b""
        for param in self.model.parameters():
            if param.grad is not None:
                grad_bytes += param.grad.cpu().detach().numpy().tobytes()
        
        return hashlib.sha256(grad_bytes).hexdigest()
    
    def train_batch(self, batch_data: torch.Tensor, batch_labels: torch.Tensor) -> Tuple[float, str]:
        """
        Train on one batch and return loss + gradient hash
        """
        self.optimizer.zero_grad()
        
        # Forward pass
        outputs = self.model(batch_data.to(self.device))
        loss = self.criterion(outputs, batch_labels.to(self.device))
        
        # Backward pass
        loss.backward()
        
        # Compute gradient hash (before optimizer step)
        grad_hash = self.hash_gradients()
        
        # Update weights
        self.optimizer.step()
        
        return loss.item(), grad_hash
    
    def train_epoch(self, epoch: int) -> list:
        """
        Train for one epoch, submit gradient proofs
        """
        self.model.train()
        batch_stats = []
        
        for batch_idx, (data, target) in enumerate(self.train_loader):
            # Compute batch hash (for ZK proof)
            batch_bytes = data.cpu().numpy().tobytes()
            batch_hash = hashlib.sha256(batch_bytes).hexdigest()
            batch_size = len(data)
            
            # Train on batch
            loss, grad_hash = self.train_batch(data, target)
            
            # Simulate gradient submission (in real system, would call aggregator)
            submission_time = time.time()
            
            # Create stat record
            stat = TrainingStats(
                epoch=epoch,
                batch=batch_idx,
                loss=loss,
                accuracy=0.0,  # Computed below
                gradient_hash=grad_hash,
                submission_time=submission_time
            )
            batch_stats.append(stat)
            
            # Log every 100 batches
            if (batch_idx + 1) % 100 == 0:
                print(f"[E{epoch}B{batch_idx}] Loss: {loss:.4f}, "
                      f"Grad: {grad_hash[:12]}..., "
                      f"Batch: {batch_hash[:12]}...")
        
        self.stats_history.extend(batch_stats)
        return batch_stats
    
    def evaluate(self) -> float:
        """Test accuracy on test set"""
        self.model.eval()
        correct = 0
        total = 0
        
        with torch.no_grad():
            for data, target in self.test_loader:
                outputs = self.model(data.to(self.device))
                _, predicted = torch.max(outputs.data, 1)
                total += target.size(0)
                correct += (predicted == target.to(self.device)).sum().item()
        
        accuracy = 100 * correct / total
        return accuracy
    
    def get_model_hash(self) -> str:
        """Hash of current model state"""
        state_bytes = b""
        for param in self.model.parameters():
            state_bytes += param.cpu().detach().numpy().tobytes()
        
        return hashlib.sha256(state_bytes).hexdigest()
    
    def save_checkpoint(self, filename: str = None):
        """Save model checkpoint"""
        if filename is None:
            filename = f"model_v{self.model_version}_{self.device_id}.pth"
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'device_id': self.device_id,
            'model_version': self.model_version,
        }, filename)
        print(f"✓ Checkpoint saved: {filename}")
    
    def load_checkpoint(self, filename: str):
        """Load model checkpoint"""
        checkpoint = torch.load(filename)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.device_id = checkpoint['device_id']
        self.model_version = checkpoint['model_version']
        print(f"✓ Checkpoint loaded: {filename}")


# ==================== Example Usage ====================

if __name__ == "__main__":
    print("=" * 70)
    print("🏋️ Federated Trainer – Local Training Demo")
    print("=" * 70)
    
    # Create trainer
    trainer = FederatedTrainer("device-trainer-001", model_version=1)
    
    print(f"\n📊 Initial Model Hash: {trainer.get_model_hash()[:16]}...")
    print(f"   Initial Accuracy: {trainer.evaluate():.2f}%")
    
    # Train for 1 epoch
    print("\n🔄 Training Epoch 1...")
    stats = trainer.train_epoch(epoch=1)
    
    print(f"\n📊 After Epoch 1:")
    print(f"   Model Hash: {trainer.get_model_hash()[:16]}...")
    print(f"   Accuracy: {trainer.evaluate():.2f}%")
    print(f"   Gradients submitted: {len(stats)}")
    
    # Save checkpoint
    trainer.save_checkpoint()
    
    print("\n✓ Training complete")
    print("=" * 70)
