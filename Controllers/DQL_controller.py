from Cars.aicar import AICar
import random
import numpy as np
import torch
from nn import NeuralNetwork
from Controllers.controller import Controller
import torch.optim as optim
from torch import nn
import pygame
from collections import deque
import json

# RL hyperparameters
GAMMA = 0.97 # Reward discount factor (lower values immediate score more)
MAX_EPSILON = 1 # Starting epsilon value
MIN_EPSILON = 0.02 # Ending epsilon value
EPSILON_DECAY = 0.0005 # Epsilon decay
ALPHA = 0.005 # How much to weight the predicting network vs optimizing network in soft update
UPDATE_MODE = 0 # 0 is hard update, 1 is soft update


STEPS_BETWEEN_TRAIN = 750 # Number of experiences needed to be collected before updating optimizing network
BATCH_SIZE = 1024 # Number of experiences to train on after collecting memory
STEPS_BETWEEN_OPTIMIZER_UPDATE = 100
LEARNING_RATE = 0.001

MIN_REPLAY_SIZE = 1024 # Minimum number of experiences in memory needed before training
MEMORY_CAPACITY = 20000

class DQL_Controller(Controller):

    def __init__(self, track, surface, brain_template):
        self.track = track
        self.surface = surface

        # Each generation is an episode (spawn -> death)
        self.generation = 1
        print("On Generation:", 1)

        # Select gpu or cpu 
        self.device = torch.device("cuda:0" if torch.cuda.is_available else "cpu") # For GPU
        # self.device = "cpu"

        # Setup NN brain template
        self.car = AICar(self.track)
        self.car.update(self.surface)
        self.brain_template = [self.car.numSensors + 1] + brain_template + [self.car.numActions]

        # Initialize the 2 networks needed for DQL
        self.predicting_network = NeuralNetwork(self.brain_template).to(self.device)
        self.optimizing_network = NeuralNetwork(self.brain_template).to(self.device)
        self.optimizing_network.load_state_dict(self.predicting_network.state_dict())
        self.optimizer = optim.Adam(self.predicting_network.parameters(), lr=LEARNING_RATE)

        self.lossFN = nn.SmoothL1Loss()

        # RL parameters
        self.epsilon = MAX_EPSILON
        self.steps_episode = 0

        # Memory for experiences
        self.memory = deque(maxlen=MEMORY_CAPACITY) # dequeue automatically handles capacity

    def update(self):
        # Show car's score
        pygame.font.init()
        font = pygame.font.SysFont('Comic Sans MS', 10)
        score_surface = font.render("Score: " + str(round(self.car.score, 3)), False, (0, 0, 0))
        self.surface.blit(score_surface, (20,50))

        # Update car and gain an experience
        experience = self._act()
        self.memory.append(experience)
        self.steps_episode += 1

        # Train once we've gone through enough experiences
        if self.steps_episode % STEPS_BETWEEN_TRAIN == 0 and len(self.memory) >= MIN_REPLAY_SIZE:
            self._train()
 
        # Epsilon decay after every learning iteration
        self._decayEpsilon()

        # If this episode is done, reset
        if not self.car.alive:
            # Update optimizing network to match the predicting one after enough training cycles
            if self.steps_episode >= STEPS_BETWEEN_OPTIMIZER_UPDATE:
                if UPDATE_MODE == 0:
                    # Hard update (copy state dict)
                    self.optimizing_network.load_state_dict(self.predicting_network.state_dict())
                    self.steps_episode = 0
                else:
                    # Soft update (partially copy state dict)
                    predicting_network_state_dict = self.predicting_network.state_dict()
                    optimizing_network_state_dict = self.optimizing_network.state_dict()
                    for key in predicting_network_state_dict:
                        optimizing_network_state_dict[key] = predicting_network_state_dict[key] * ALPHA + optimizing_network_state_dict[key] * (1 - ALPHA)
                    self.optimizing_network.load_state_dict(optimizing_network_state_dict)

            self._nextGeneration()
            self.generation += 1
            print("Epsilon:", self.epsilon)
            print("On Generation:", self.generation)


    def _train(self):
        # Create training batch of experiences to train on
        # np.random.shuffle(self.memory)
        # sampled_experiences = self.memory[0:BATCH_SIZE]
        sampled_experiences = random.sample(self.memory, BATCH_SIZE)

        # Attempt at vectorizing training
        batch = list(zip(*sampled_experiences))
        old_states, actions, new_states, rewards, done = batch[0], batch[1], batch[2], batch[3], batch[4]
        old_states = torch.stack(old_states)
        new_states = torch.stack(new_states)
        rewards = torch.tensor(rewards, device=self.device)
        actions = torch.tensor(actions, device=self.device)
        done = torch.tensor(done, device=self.device)
        notdone = ~done

        Q_predictions = self.predicting_network(old_states)
        Q_samples = Q_predictions[torch.arange(BATCH_SIZE), actions]

        Q_targets_notdone = torch.zeros(BATCH_SIZE, device=self.device)

        with torch.no_grad():
            Q_targets_notdone[notdone] = self.optimizing_network(new_states[notdone]).max(1).values
        Q_targets = (Q_targets_notdone * GAMMA) + rewards
        

        # for experience in sampled_experiences:
        #     # Forward pass
        #     old_s, a, new_s, r, done = experience

        #     Q_sample = Q_samples[a]
        #     Q_target = r if done else (r + (GAMMA * torch.max(Q_new_samples)[0]))


        #     y_train.append(Q_sample)
        #     y_test.append(Q_target)

        # y_train = torch.tensor(y_train).to(self.device)
        # y_test = torch.tensor(y_test).to(self.device)

        loss = self.lossFN(Q_samples, Q_targets)
        # print("loss:", loss)
        # print(y_train)
        # print(y_test)

        # Backword pass
        self.optimizer.zero_grad()
        loss.backward()

        # Gradient clipping
        torch.nn.utils.clip_grad_value_(self.predicting_network.parameters(), 100)
        self.optimizer.step()

    def _getLoss(self, Q_sample, Q_target):
        return torch.square(torch.subtract(Q_sample, Q_target))

    def _act(self):
        """Obtains one experience from the car

        The car takes one action which is recorded
        
        Returns:
            (old_state, action, new_state, reward, done) 
            old_state: torch.Tensor
            action: torch.Tensor(a)
            new_state: torch.Tensor
            reward: float
            done: boolean

            Where Q() is the predicting network and Q'() is the optimizing network
        """
        old_score = self.car.score
        state = torch.tensor(self.car.getState(), device=self.device)

        # Pick action based on epsilon greedy
        action = self._selectAction(state)

        # Update car based on chosen action
        self.car.update(self.surface, action=action)

        new_score = self.car.score
        
        reward = new_score - old_score
        new_state = torch.tensor(self.car.getState(), device=self.device)

        done = self.car.alive

        return (state, action, new_state, reward, done)
    

    def _selectAction(self, state):
        # Pick action based on epsilon greedy
        Q_samples = self.predicting_network(state)
        action = -1
        rand = random.random()
        if rand < self.epsilon:
            action = torch.tensor([random.randint(0, self.car.numActions - 1)], device=self.device)
        else:
            with torch.no_grad():
                action = torch.argmax(Q_samples)
        return action

    def _nextGeneration(self):
        self.car.reset()
        self.car.update(self.surface)

    def _decayEpsilon(self):
        self.epsilon = MIN_EPSILON + (MAX_EPSILON - MIN_EPSILON) * np.exp(-1 * EPSILON_DECAY * self.generation)
        # self.epsilon = max(MIN_EPSILON, self.epsilon - EPSILON_DECAY)
        # print("epsilon:", self.epsilon)


    def save(self):
        torch.save(self.predicting_network.state_dict(), './Cars/DQL_car_brain.pth')
        saveFile = json.dumps({
            "epsilon": self.epsilon,
            "generation": self.generation,
        })
        torch.save(self.memory, './Cars/DQL_car_memory.pth')

        print(saveFile) # TODO: save json to file

    def load(self):
        # Initialize the 2 networks needed for DQL
        self.predicting_network = NeuralNetwork(self.brain_template).to(self.device)
        self.optimizing_network = NeuralNetwork(self.brain_template).to(self.device)

        self.predicting_network.load_state_dict(torch.load('./Cars/DQL_car_brain.pth'))
        self.optimizing_network.load_state_dict(self.predicting_network.state_dict())
        self.optimizer = optim.Adam(self.predicting_network.parameters(), lr=LEARNING_RATE)

        save = json.loads(open('./Cars/DQL_car_data.json', 'r').read())
        self.epsilon = save["epsilon"]
        self.generation = save["generation"]

        self.memory = torch.load('./Cars/DQL_car_memory.pth')