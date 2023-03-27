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

    def estimate_sources_of_attack(self, demo_sightings):
        #determine MLE for position that demos are being launched from
        projections = []
        lhs = { 0: 14, 1 : 15, 2 : 16, 3 : 17, 4 : 18, 5 : 19, 6: 20, 7 : 21, 8 : 22, 9 : 23, 10 : 24, 11 : 25, 12: 26, 13: 27}
        rhs = { 14 : 27, 15: 26, 16: 25, 17: 24, 18: 23, 19: 22, 20 : 21, 21: 20, 22 : 19, 23 : 18, 24: 17, 25 : 16, 26: 15, 27: 14}

        estimated_left_sources = []
        estimated_right_sources = []

        for s in demo_sightings:
            sm = s[0] + s[1]
            if(s[0] > 13):
                estimated_source = []
                for k in lhs.keys():
                    if(lhs[k] + k == sm):
                        estimated_source = [k, lhs[k]]
                        break
                
                estimated_left_sources.append(estimated_source)
            elif(s[0] < 13):
                estimated_source = []
                d = float('inf')
                for k in rhs.keys():
                    if(d > abs(s[0] - k) + abs(s[1] - rhs[k]) ):
                        d = abs(s[0] - k) + abs(s[1] - rhs[k])
                        estimated_source = [k, rhs[k]]
                
                estimated_right_sources.append(estimated_source)

            
            return (estimated_left_sources, estimated_right_sources)
            

    def compute_optimal_demo_allocations(self, game_state, demo_sightings, scout_sightings = None, interceptor_sightings = None):
        #determine optimal demo allocations to attack enemy defenses

        estimated_left_sources, estimated_right_sources = self.estimate_sources_of_attack(demo_sightings)
        #estimated_left_sources_scout, estimated_right_sources_scout = self.estimate_sources_of_attack(scout_sightings)
        #estimated_left_sources_interceptor, estimated_right_sources_interceptor = self.estimate_sources_of_attack(interceptor_sightings)

        denom = max(len(estimated_right_sources), 1)
        density = (len(estimated_left_sources)/denom) * (len(estimated_left_sources))

        x1 = sum([e[0] for e in estimated_left_sources])/len(estimated_left_sources)
        y1 = sum([e[1] for e in estimated_left_sources])/len(estimated_left_sources)
        x2 = sum([e[0] for e in estimated_right_sources])/len(estimated_right_sources)
        y2 = sum([e[1] for e in estimated_right_sources])/len(estimated_right_sources)
        
        targets = [ [x1, y1], [x2, y2] ]

        starting_positions = [ [0, 13], [1, 12], [2, 11], [3, 10], [4, 9], [5, 8], [6, 7], [7, 6], [8, 5], [9, 4], [10, 3], [11, 2], [12, 1], [13, 0]
                               [14, 0], [15, 1], [16, 2], [17, 3], [18, 4], [19, 5], [20, 6], [21, 7], [22, 8], [23, 9], [24, 10], [25, 11], [26, 12], [27,13] ]
        
        
        returned_positions = []
        desired_configuration = []

        found = False
        for target in targets:
            opt_position = []
            dev = float('inf')
            for position in starting_positions:
                path = game_state.find_path_to_edge(position)
                endpoint = path[len(path)-1]
                val = abs(endpoint[0] - target[0]) + abs(endpoint[1] - target[1])
                if(min(dev, val) == val):
                    opt_position = position
            
            returned_positions.append(opt_position)

        
        base = 2
        left_demo_size = density*base
        right_demo_size = base

        return (returned_positions, left_demo_size, right_demo_size)
        
    


