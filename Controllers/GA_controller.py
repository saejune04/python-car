from Cars.aicar import AICar
import random
import torch
from nn import NeuralNetwork
from Controllers.controller import Controller

TOP_N = 7 # Number of top cars to keep in each generation to cross breed
MUTATION_RATE = 0.1
CROSSOVER_RATE = 0.8 # Probability child takes gene from parent 1 vs parent 2
BLANKS_PER_GEN = 5
MUTANTS_PER_GEN = TOP_N # Number of mutations to make from the top_n cars from the last generation

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
        dummy_car = AICar(self.track, device=self.device)
        self.brain_template = [dummy_car.numSensors + 1] + brain_template + [dummy_car.numActions]

        self.cars = []
        self.generation = 0
        self.bestCar = None
        self.bestScore = -100
        assert TOP_N + BLANKS_PER_GEN + MUTANTS_PER_GEN < num_cars


    def update(self):
        """Updates all cars this controller controls
        
        Handles generations and updating each car in the current generation.
        Should be called once every frame
        """
        if self.generation == 0:
            self._initFirstGeneration()
            self.generation += 1
        num_dead = 0
        for i in range(1, self.num_cars):
            car = self.cars[i]
            car.update(self.surface)
            if not car.alive:
                num_dead += 1
        self.cars[0].update(self.surface, leader=True)
        if not self.cars[0].alive:
            num_dead += 1

        if num_dead == self.num_cars:
            self.generation += 1
            self._nextGeneration()

    def _initFirstGeneration(self):
        """Initializes the first generation
        
        Fills the first generation with randomly initialized cars. If a car was loaded in,
        Replaces one of the randomly initialized cars with the loaded one.
        """
        self.cars = []
        if self.bestCar:
            self.cars.append(self.bestCar)
        for _ in range(self.num_cars - len(self.cars)):
            newcar = AICar(self.track, self.device, self.brain_template)
            self.cars.append(newcar)

    def _nextGeneration(self):
        """Sets up the next generation of cars
        
        Should be called once all cars from the previous generation are done running
        """
        # Get the TOP_N best cars of the last generation
        sorted_cars = sorted(self.cars, key = lambda x: x.score, reverse = True)
        top_n_cars = sorted_cars[:TOP_N]

        # Erase all cars from the last generation
        self.cars = []

        # Update global best car if better car exists and add to next gen cars
        if top_n_cars[0].score > self.bestScore:
            self.bestScore = top_n_cars[0].score
            self.bestCar = top_n_cars[0]
        else:
            # No better car exists, use existing best car
            self.cars.append(self.bestCar)

        ###################### Add next gen cars!! ######################
        # First add best cars from last generation
        self.cars = self.cars + top_n_cars[len(self.cars) : TOP_N] # Exclude last gen's best car if it is the new global best car

        # Add blank cars for gene diversity
        for _ in range(BLANKS_PER_GEN):
            self.cars.append(AICar(self.track, device=self.device, brain_template=self.brain_template))

        # Add cars that are slightly mutated from the top_n cars of previous generations
        for _ in range(MUTANTS_PER_GEN):
            mutate_index = random.randint(0, TOP_N - 1)
            car_to_mutate = self.cars[mutate_index]
            mutated_car = AICar(self.track, device=self.device, brain_template=self.brain_template)
            mutated_car.brain = self._mutate(car_to_mutate.brain)
            self.cars.append(mutated_car)

        # Cross-breed best cars with other cars for the rest of the generation
        num_cars_to_breed = self.num_cars - len(self.cars)
        for _ in range(num_cars_to_breed):
            ran1 = random.randint(0, TOP_N - 1)
            ran2 = random.randint(0, len(self.cars) - 1)
            self.cars.append(self._crossbreed(self.cars[ran1], self.cars[ran2]))
        
        print('On generation', self.generation)

    def _crossbreed(self, car1, car2):
        """Creates a child car using information from 2 cars
        
        Args:
            car1: First parent car
            car2: Second parent car
        Returns:
            child: an AICar whose brain is a mixture of both parents with mutations
                   as dictated by CROSSOVER_RATE and MUTATION_RATE
        """
        brain1 = car1.brain.state_dict()
        brain2 = car2.brain.state_dict()

        child_brain = self._crossover(brain1, brain2)
        child = AICar(self.track, device=self.device, brain_template=self.brain_template)
        child.brain.load_state_dict(child_brain)
        child.brain = self._mutate(child.brain).to(child.device)
        return child

    def _crossover(self, brain1, brain2):
        child_brain = {}

        for key in brain1.keys():
            if random.random() < CROSSOVER_RATE:
                child_brain[key] = brain1[key].clone()
            else:
                child_brain[key] = brain2[key].clone()

        return child_brain
    
    def _mutate(self, brain):
        for param in brain.parameters():
            if torch.rand(1).item() < MUTATION_RATE:
                param.data += torch.randn_like(param.data) * 0.1  # Adding Gaussian noise with std=0.1
        return brain
    
    def saveBestModel(self):
        torch.save(self.bestCar.brain.state_dict(), './Cars/best_car.pth')
        print("Model's best score: ", self.bestScore)

    def loadBestModel(self):
        self.bestCar = AICar(self.track, device=self.device, brain_template=self.brain_template)
        self.bestCar.brain.load_state_dict(torch.load('./Cars/best_car.pth'))
        self.bestCar.brain.eval()  # Set the model to evaluation mode
        self.cars = []
        self.cars.append(self.bestCar)
        self.bestScore = float(input("Input the model's best score: "))
        