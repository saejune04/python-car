from Cars.aicar import AICar
import random
import torch
from nn import NeuralNetwork
from Controllers.controller import Controller

TOP_N = 7 # Number of top cars to keep in each generation to cross breed
MUTATION_RATE = 0.1
CROSSOVER_RATE = 0.7 # Probability child takes gene from parent 1 vs parent 2
BLANKS_PER_GEN = 5
MUTANTS_PER_GEN = TOP_N # Number of mutations to make from the top_n cars from the last generation

EPSILON = 0.02 # Chance that a car takes a completely random action on a given update

class GA_Controller(Controller):
    # Genetic algorithm
    def __init__(self, track, surface, brain_template, num_cars=50):
        self.track = track
        self.num_cars = num_cars
        self.surface = surface

        # Select gpu or cpu (gpu not recommended atm)
        # self.device = torch.device("cuda:0" if torch.cuda.is_available else "cpu") # For GPU
        self.device = "cpu"

        # Setup NN brain template
        dummy_car = AICar(self.track)
        self.brain_template = [dummy_car.numSensors + 1] + brain_template + [dummy_car.numActions]

        self.cars = [] # List of (AICar, brain)
        self.generation = 0
        self.bestBrain = None
        self.bestScore = -100
        assert TOP_N + BLANKS_PER_GEN + MUTANTS_PER_GEN < num_cars
        assert TOP_N > 0


    def update(self):
        """Updates all cars this controller controls
        
        Handles generations and updating each car in the current generation.
        Should be called once every frame
        """
        if self.generation == 0:
            self._initFirstGeneration()
            self.generation += 1
            print('On generation', self.generation)

        num_dead = 0

        for car, brain in self.cars:
            if not car.alive:
                num_dead += 1
            else:
                car_state = torch.tensor(car.getState()).to(self.device)
                action = torch.argmax(brain(car_state)).item()
                car.update(self.surface, action=action, epsilon=EPSILON)

        # Start next generation if all cars are dead from last generation
        if num_dead == self.num_cars:
            self.generation += 1
            self._nextGeneration()
            print('On generation', self.generation)


    def _initFirstGeneration(self):
        """Initializes the first generation
        
        Fills the first generation with randomly initialized cars. If a car was loaded in,
        Replaces one of the randomly initialized cars with the loaded one.
        """
        self.cars = []

        if self.bestBrain:
            new_car = AICar(self.track)
            new_car.update(self.surface)
            self.cars.append((new_car, self.bestBrain))
        
        num_cars_needed = self.num_cars - len(self.cars)
        for _ in range(num_cars_needed):
            new_car = AICar(self.track)
            new_car.update(self.surface)
            new_brain = NeuralNetwork(self.brain_template).to(self.device)
            self.cars.append((new_car, new_brain))

    def _nextGeneration(self):
        """Sets up the next generation of cars
        
        Should be called once all cars from the previous generation are done running
        """
        # Get the TOP_N best cars of the last generation
        sorted_cars = sorted(self.cars, key = lambda x: x[0].score, reverse = True)
        top_n_cars = sorted_cars[:TOP_N]

        # Erase all cars from the last generation
        self.cars = []

        # Update global best car if better car exists and add to next gen cars
        if top_n_cars[0][0].score > self.bestScore:
            self.bestScore = top_n_cars[0][0].score
            self.bestBrain = top_n_cars[0][1]
        else:
            # No better car exists, use existing best car
            self.cars.append((AICar(self.track), self.bestBrain))

        ###################### Add next gen cars!! ######################
        # First add best cars from last generation
        self.cars = self.cars + top_n_cars[len(self.cars) : TOP_N] # Exclude last gen's best car if it is the new global best car

        # Add blank cars for gene diversity
        for _ in range(BLANKS_PER_GEN):
            new_brain = NeuralNetwork(self.brain_template)
            self.cars.append((AICar(self.track), new_brain))

        # Add cars that are slightly mutated from the top_n cars of previous generations
        for _ in range(MUTANTS_PER_GEN):
            mutate_index = random.randint(0, TOP_N - 1)
            brain_to_mutate = self.cars[mutate_index][1]
            mutated_brain = self._mutate(brain_to_mutate)
            self.cars.append((AICar(self.track), mutated_brain))

        # Cross-breed best cars with other cars for the rest of the generation
        num_cars_to_breed = self.num_cars - len(self.cars)
        for _ in range(num_cars_to_breed):
            ran1 = random.randint(0, TOP_N - 1)
            ran2 = random.randint(0, len(self.cars) - 1)
            self.cars.append((AICar(self.track), self._crossbreed(self.cars[ran1][1], self.cars[ran2][1])))
        
        # Set all brains to current device and call update once for each car
        for car, brain in self.cars:
            car.update(self.surface)
            brain.to(self.device)
            
    def _crossbreed(self, brain1, brain2):
        """Creates a child brain using information from 2 brains
        
        Args:
            brain1: First parent brain
            brain2: Second parent brain
        Returns:
            child: a brain is a mixture of both parents with mutations
                   as dictated by CROSSOVER_RATE and MUTATION_RATE
        """
        brain1 = brain1.state_dict()
        brain2 = brain2.state_dict()

        child_brain = self._crossover(brain1, brain2)
        child_brain = self._mutate(child_brain)
        return child_brain

    def _crossover(self, brain1, brain2):
        child_brain_state = {}

        for key in brain1.keys():
            if random.random() < CROSSOVER_RATE:
                child_brain_state[key] = brain1[key].clone()
            else:
                child_brain_state[key] = brain2[key].clone()
        child_brain = NeuralNetwork(self.brain_template)
        child_brain.load_state_dict(child_brain_state)
        return child_brain
    
    def _mutate(self, brain):
        for param in brain.parameters():
            if torch.rand(1).item() < MUTATION_RATE:
                param.data += torch.randn_like(param.data) * 0.1  # Adding Gaussian noise with std=0.1
        return brain
    
    def save(self):
        torch.save(self.bestBrain.state_dict(), './Cars/GA_car_brain.pth')
        print("Model's best score: ", self.bestScore)

    def load(self):
        self.bestBrain = NeuralNetwork(self.brain_template)
        self.bestBrain.load_state_dict(torch.load('./Cars/GA_car_brain.pth'))
        self.bestBrain.to(self.device)
        self.bestBrain.eval()  # Set the model to evaluation mode

        self.bestScore = float(input("Input the model's best score: "))
        