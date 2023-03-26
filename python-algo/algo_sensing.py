import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from collections import defaultdict
import algo_strategy

class AlgoSense(algo_strategy.AlgoStrategy):

    def __init__(self):
        super(algo_strategy.AlgoStrategy, self).__init__()

    def estimate_source_of_attack(self, demo_sightings):
        #determine MLE for position that demos are being launched from

        pass

    
    def compute_optimal_demo_allocations(self, demo_sightings):
        #determine optimal demo allocations to attack enemy defenses

        pass

