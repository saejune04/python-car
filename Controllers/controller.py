from abc import ABC, abstractmethod

class Controller(ABC):
    """Abstract class for a controller
    
    A controller should handle everything within a single update method that is
    called every frame.
    """

    @abstractmethod
    def update(self):
        """Updates everything for the frame"""
        pass