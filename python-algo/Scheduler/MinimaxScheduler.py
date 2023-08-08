import os
import sys
import subprocess
from map_data_structures import Structure

class MinimaxScheduler:
    '''
    A minimax scheduler which is a function of the current view of the map and some utility function to maximize
    (or minimize as the opponent) i.e. a zero-sum game.
    '''
    def __init__(self, s1 : Structure, s2: Structure, utility_func: function):
        self.s1 = s1
        self.s2 = s2
        self.utility_func = utility_func
        
    
    def simulate(self):
        pass
    
    