import numpy as np
import torch
import torch.nn as nn

class NeuralNetwork(nn.Module):
    def __init__(self, dimensions):
        """Constructs a neural network with layers based on given dimensions
        
        Args:
            dimensions: a list of numbers representing the dimensions of the layers
                        dimensions[0] should be the input size and dimensions[-1] 
                        should be the output size
        """
        super(NeuralNetwork, self).__init__()
        layers = []
        
        for i in range(len(dimensions) - 1):
            layers.append(nn.Linear(dimensions[i], dimensions[i + 1]))
            if i < len(dimensions) - 2:  # No activation function on the output layer
                layers.append(nn.ReLU())
        layers.append(nn.Softmax(dim=0))
        self.network = nn.Sequential(*layers)
    
    def forward(self, x):
        return self.network(x)