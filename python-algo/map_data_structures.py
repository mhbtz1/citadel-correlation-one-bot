import numpy as np
import os
import subprocess
import copy
from typing import List, Tuple

class Structure:
    def __init__(self, defenses : List[Tuple], offenses : List[Tuple]):
        self.defense_pos = defenses
        self.offense_pos = offenses
        

        
