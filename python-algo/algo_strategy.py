import gamelib
import random
import math
import warnings
from sys import maxsize
import json
from collections import defaultdict
import algo_sensing

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP, senser, removed_positions
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = [] #locations that the enemy has scored on
        self.locations_scored_on = [] #locations we have scored on in the past

        self.recent_points_of_attack = [] #locations of recent points our units have been attacked from
        self.placed_units = defaultdict(tuple) #dictionary mapping position to if it is currently placed
        self.turret_last_upgrade = defaultdict(int)
        self.wall_last_upgrade = defaultdict(int)


        self.TURRET_LIMIT_PER_TURN = 4 #limit for number of turrets we build per turn
        self.TURRET_UPGRADE_LIMIT_PER_TURN = 2
        self.WALL_UPGRADE_LIMIT_PER_TURN = 8

        self.TURRET_BUILD_COOLDOWN = 4
        self.WALL_BUILD_COOLDOWN = 2
        self.LAST_WALL_TIME = -1
        self.LAST_TURRET_TIME = -1

        self.ATTACK_COOLDOWN = 3
        self.last_attack = -1

        self.rush_flag_status = 1 #will indicate how to randomize our offence strategy
        self.defence_flag_status = 1 #will indicate how to randomize our defence strategy

        removed_positions = [ [ [9, 11], [13, 11] ], [ [8, 11], [12, 11] ], [ [10, 11], [14, 11] ], 
                            [ [11, 11], [15, 11] ], [ [9, 11], [13, 11], [17, 11] ], [ [13, 11] ], [ [10, 11] ], [ [15, 11] ] ]

        #arrangement of turrets and walls ordered by preference of building
        self.structure_one = [ ([3, 12], 'T'), ([24, 12], 'T'), ( [0, 13], 'T'), ( [27, 13], 'T'), ( [9, 13], 'T'), ( [17, 13], 'T'), ([6, 9], 'W'), ([7, 9], 'W'), ([7, 12], 'T'), ([19, 12], 'T'), ([20, 9], 'W'), ([21, 9], 'W'), ([8, 11], 'W'), ([9, 11], 'W'), ([10, 11], 'W'), ([11, 11], 'W'), ([12, 11], 'W'),([13, 11], 'W'), ([14, 11], 'W'), ([15, 11], 'W'), ([16, 11], 'W'), ([17, 11], 'W'), ([18, 11], 'W'), ([5, 11], 'T'), ([21, 11], 'T'), ([7, 11], 'T'), ([19, 11], 'T') ]
        #arrangement of preferenes over turret upgrades (can be rearranged by heuristics later based on attacked sides)
        self.structure_one_upgrade_preference = [ ([3, 12], 'T'), ([24, 12], 'T'), ( [0, 13], 'T'), ( [27, 13], 'T'), ( [9, 13], 'T'), ( [17, 13], 'T'), ([6, 9], 'W'), ([7, 9], 'W'), ([7, 12], 'T'), ([19, 12], 'T'), ([20, 9], 'W'), ([21, 9], 'W'), ([8, 11], 'W'), ([9, 11], 'W'), ([10, 11], 'W'), ([11, 11], 'W'), ([12, 11], 'W'),([13, 11], 'W'), ([14, 11], 'W'), ([15, 11], 'W'), ([16, 11], 'W'), ([17, 11], 'W'), ([18, 11], 'W'), ([5, 11], 'T'), ([21, 11], 'T'), ([7, 11], 'T'), ([19, 11], 'T') ]
        self.structure_one_gapped_walls = []


        self.structure_two = []
        self.structure_two_upgrade_preference = []

        senser = algo_sensing.AlgoSense()


    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.
        
        for k in self.placed_units.keys():
            if(not game_state.contains_stationary_unit([k[0], k[1]]) ):
                self.placed_units[ (k[0], k[1]) ] = False

        attacking_demos = []
        attacking_interceptors = []
        attacking_scouts = []
        
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location) and game_state.game_map[location][0].player_index == 0:
                atkr = game_state.get_attackers(location, 0)
                for atk in atkr:
                    if(atk.unit_type == DEMOLISHER):
                        attacking_demos.append([atk.x, atk.y])
                    if(atk.unit_type == SCOUT):
                        attacking_scouts.append([atk.x, atk.y])
                    if(atk.unit_type == INTERCEPTOR):
                        attacking_interceptors.append([atk.x, atk.y])
            
        gamelib.debug_write("Current detected attacking demolishers: {}".format(attacking_demos))

        if(game_state.turn_number < 1000):
            self.heuristic_rush_strategy(game_state)
        else:
            self.deterministic_rush_strategy(game_state, attacking_demos, attacking_interceptors, attacking_scouts)
        
        self.defence_strategy(game_state)
        
        self.on_action_frame(turn_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # First, place basic defenses
        self.build_defences(game_state)
        # Now build reactive defenses based on where the enemy scored
        self.build_reactive_defense(game_state)

        # If the turn is less than 5, stall with interceptors and wait to see enemy's base
        if game_state.turn_number < 5:
            self.stall_with_interceptors(game_state)
        else:
            # Now let's analyze the enemy base to see where their defenses are concentrated.
            # If they have many units in the front we can build a line for our demolishers to attack them at long range.
            if self.detect_enemy_unit(game_state, unit_type=None, valid_x=None, valid_y=[14, 15]) > 10:
                self.demolisher_line_strategy(game_state)
            else:
                # They don't have many units in the front so lets figure out their least defended area and send Scouts there.

                # Only spawn Scouts every other turn
                # Sending more at once is better since attacks can only hit a single scout at a time
                if game_state.turn_number % 2 == 1:
                    # To simplify we will just check sending them from back left and right
                    scout_spawn_location_options = [[13, 0], [14, 0]]
                    best_location = self.least_damage_spawn_location(game_state, scout_spawn_location_options)
                    game_state.attempt_spawn(SCOUT, best_location, 1000)

                # Lastly, if we have spare SP, let's build some supports
                support_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
                game_state.attempt_spawn(SUPPORT, support_locations)

    def defense_heuristic_state(self, game_state):
        heuristic_value = 0
        for loc in game_state.game_map:
            if(game_state.contains_stationary_unit(loc) and game_state.game_map[loc][0].player_index == 0 and game_state.game_map[loc][0].unit_type == TURRET):
                heuristic_value += 10
            elif(game_state.contains_stationary_unit(loc) and game_state.game_map[loc][0].player_index == 0 and game_state.game_map[loc][0].unit_type == WALL):
                heuristic_value += 2

        return heuristic_value

    def randomized_demolisher_openings(self, game_state):
        #positions to randomize with: 8 through 18 (allow for demolisher charges and rerouting for general units)

        desired_wall_orientation = []

        num_opening = random.randint(0, len(removed_positions)-1)

        rem = removed_positions[num_opening]
        compr = [r[0] for r in rem]

        for i in range(8, 19):
            if(i in compr):
                continue
            desired_wall_orientation.append([i, 11])
        
        self.structure_one_gapped_walls = rem
        
        return (desired_wall_orientation, rem)
    

    def deterministic_rush_strategy(self, game_state, demo_sightings, scout_sightings = None, interceptor_sightings = None):
        #determine optimal demolisher opening to let demolishers to target proper enemy cells
        desired_wall_orientation = []

        (positions, left_size, right_size) = senser.compute_optimal_demo_allocations(game_state, demo_sightings)

        game_state.attempt_spawn(DEMOLISHER, positions[0],  left_size)
        game_state.attempt_spawn(DEMOLISHER, position[1], right_size)

        return desired_wall_orientation
    
    def random_troop_allocation(self, game_state, troop_type, amount):
        troop = 0
        if(troop_type == 0):
            troop = SCOUT
        elif(troop_type == 1):
            troop = DEMOLISHER
        elif(troop_type == 2):
            troop = INTERCEPTOR

        for _ in range(amount):
            r = random.uniform(0,1)
            if(r < 0.5):
                p = random.randint(0, 13)
                game_state.attempt_spawn(troop, [p, 13 - p], 1)
                gamelib.debug_write("Case One: Placing demolisher at position {}, {}".format(p, 13-p))

            elif (r >= 0.5):
                p = (int)(random.randint(0, 13))
                d = {0 : 14, 1 : 15, 2 : 16, 3: 17, 4 : 18, 5 : 19, 6: 20, 7 : 21, 8 : 22, 9 : 23, 10: 24, 11: 25, 12: 26, 13: 27}
                game_state.attempt_spawn(troop, [d[p], p], 1)
                gamelib.debug_write("Case Two: Placing demolisher at position {}, {}".format(d[p], p))


    def heuristic_rush_strategy(self, game_state, optimal_demo_locations = None):
        current_defense_heuristic = self.defense_heuristic_state(game_state)
        gamelib.debug_write("Current defense heuristic value: {}".format(current_defense_heuristic))
        if(self.rush_flag_status == 1): #random small scout placement
            r = random.uniform(0, 1)
            amount = math.floor(random.normalvariate(6, 1))

            if(r < 0.80):
               #randomize between interceptors and demolishers based on defense heuristic (helps to contend against mass losses in defense)
                param = 0
                if(current_defense_heuristic < 25):
                    param = 1
                elif(25 < current_defense_heuristic < 40):
                    param = 0.9
                elif(40 < current_defense_heuristic < 65):
                    param = 0.5
                elif(65 < current_defense_heuristic < 100):
                    param = 0.1
               
                r2 = random.uniform(0,1)
            
                if(r2 < param):
                  if(game_state.turn_number - self.last_attack >= self.ATTACK_COOLDOWN): 
                        self.random_troop_allocation(game_state, 2, amount)
                        self.last_attack = game_state.turn_number
                else:
                  if(game_state.turn_number - self.last_attack >= self.ATTACK_COOLDOWN * 2):
                        game_state.attempt_spawn(DEMOLISHER, [13, 0], 5)
            else:
                
                valid_pos = []
                if(game_state.contains_stationary_unit([6, 9]) and game_state.contains_stationary_unit([7, 9]) ):
                    valid_pos.append([14, 0])
                elif(game_state.contains_stationary_unit([20, 9]) and game_state.contains_stationary_unit([21, 9])):
                    valid_pos.append([13, 0])
                
                if(valid_pos != []):
                    r = random.randint(0,len(valid_pos)-1)
                    game_state.attempt_spawn(SCOUT, valid_pos[r], 1000)
                
                
                self.rush_flag_status = 3

        elif(self.rush_flag_status == 2): #demo rush
            if(game_state.get_resources(0)[1] >= 30):
                valid_pos = []
                if(game_state.contains_stationary_unit([6, 9]) and game_state.contains_stationary_unit([7, 9]) ):
                    valid_pos.append([14, 0])
                elif(game_state.contains_stationary_unit([20, 9]) and game_state.contains_stationary_unit([21, 9])):
                    valid_pos.append([13, 0])
                
                if(valid_pos != []):
                    r = random.randint(0,len(valid_pos)-1)
                    game_state.attempt_spawn(DEMOLISHER, valid_pos[r], 1000)
            

            if(current_defense_heuristic < 25):#if our defense is in bad shape, switch to strategy 1
                self.rush_flag_status = 1
            else:
                self.rush_flag_status = 3
                

        elif(self.rush_flag_status == 3): #reconfigure demolisher line
            (wall_build, wall_remove) = self.randomized_demolisher_openings(game_state)
            build_req = []
            delete_req = []
            for q in wall_build:
                if(not game_state.contains_stationary_unit(q)):
                    build_req.append(q)
            for q in wall_remove:
                if(game_state.contains_stationary_unit(q)):
                    delete_req.append(q)
            
            if(len(build_req) > 0):
                game_state.attempt_spawn(WALL, build_req)
            if(len(delete_req) > 0):
                game_state.attempt_remove(delete_req)

            if(current_defense_heuristic < 25):
                self.rush_flag_status = 1
            else:
                self.rush_flag_status = 5

        elif(self.rush_flag_status == 4): #game initial offence
            self.random_troop_allocation(game_state, 2, 5) #should use these for intel (somehow?)
            self.rush_flag_status = 1
        
        elif(self.rush_flag_status == 5): #conserve mobile points for rushes
            
            if(game_state.get_resources(0)[1] >= 30 and current_defense_heuristic > 25):
                self.rush_flag_status = 2
            else:
                self.rush_flag_status = 1


    

    def defence_strategy(self, game_state):
        #note: consider some self-destruct trap tactics (similar to boss 3) ?

        if(game_state.get_resources(0)[0] < 6):
            return

        turret_cost = 6
        turret_upgrade = 4
        wall_cost = 0.5
        wall_upgrade = 1
        
        #randomized turret + wall placement
        if(self.defence_flag_status == 1): #use first structure

            built_turrets = 0
            upgraded_turrets = 0
            upgraded_walls = 0

            turret_limits = self.TURRET_LIMIT_PER_TURN #only build at most 4 turrets per turn
            turret_upgrade_limits = self.TURRET_UPGRADE_LIMIT_PER_TURN
            wall_upgrade_limits = self.WALL_UPGRADE_LIMIT_PER_TURN

            current_resources = game_state.get_resources(0)[0]
            turret_locs = []
            wall_locs = []
            turret_upgrade_locs = []
            wall_upgrade_locs = []

            used_resources = 0

            #if a turret is at sufficiently low health

            
            for p in self.structure_one:
                position = p[0]
                unit_type = p[1]
                if(unit_type == 'T'):
                    if(built_turrets >= turret_limits):
                        continue


                    if( (not game_state.contains_stationary_unit(position)) and used_resources + turret_cost < current_resources):
                        used_resources += turret_cost
                        built_turrets += 1
                        turret_locs.append(position)
                        self.placed_units[(position[0], position[1])] = True
                    elif(game_state.turn_number - self.turret_last_upgrade[(position[0], position[1])] > 6 and upgraded_turrets < turret_upgrade_limits and game_state.contains_stationary_unit(position) and  not game_state.game_map[position][0].upgraded ):
                        used_resources += turret_upgrade
                        upgraded_turrets += 1
                        turret_upgrade_locs.append(position)
                        self.placed_units[(position[0], position[1])] = True
                        self.turret_last_upgrade[(position[0], position[1])] = game_state.turn_number


                elif(unit_type == 'W'):
                    if(position in self.structure_one_gapped_walls):
                        continue

                    if( (not game_state.contains_stationary_unit(position)) and used_resources + wall_cost < current_resources):
                        used_resources += wall_cost
                        wall_locs.append(position)
                        self.placed_units[(position[0], position[1])] = True
                    elif(game_state.turn_number - self.wall_last_upgrade[(position[0], position[1])] > 3 and upgraded_walls < wall_upgrade_limits and game_state.contains_stationary_unit(position) and not game_state.game_map[position][0].upgraded ):
                        #modify wall upgrade heuristic to only upgrade walls at positions (6, 9), (7, 9), (20, 9), (21, 9)

                        if(position in [ [6, 9], [7, 9], [20, 9], [21, 9] ]):
                            used_resources += wall_upgrade
                            wall_upgrade_locs.append(position)
                            self.placed_units[(position[0], position[1])] = True
                            self.wall_last_upgrade[(position[0], position[1])] = game_state.turn_number
      

            game_state.attempt_spawn(TURRET, turret_locs)
            game_state.attempt_spawn(WALL, wall_locs)
            game_state.attempt_upgrade(turret_upgrade_locs)
            game_state.attempt_upgrade(wall_upgrade_locs)


        elif(self.defence_flag_status == 2): #use second structure
            pass

        elif(self.defence_flag_status == 3): #use third structure
            pass

    
    def health_at_position(self, game_state, location):
        return game_state.game_map[location][0].health

    def enemies_at_position(self, game_state, location):
        if( (game_state.game_map[location[0], location[1]])[0].player_index == 1 ):
            return (True, game_state.game_map[location])
        else:
            return (False, [])

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


    
    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[0, 13], [27, 13], [8, 11], [19, 11], [13, 11], [14, 11]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)
        
        # Place walls in front of turrets to soak up damage for them
        wall_locations = [[8, 12], [19, 12]]
        game_state.attempt_spawn(WALL, wall_locations)
        # upgrade walls so they soak more damage
        game_state.attempt_upgrade(wall_locations)

    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            game_state.attempt_spawn(TURRET, build_location)

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)
        
        # Remove locations that are blocked by our own structures 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]
            
            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    def demolisher_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our demolisher can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [WALL, TURRET, SUPPORT]
        cheapest_unit = WALL
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.MP] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.MP]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our demolisher from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn demolishers next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(DEMOLISHER, [24, 10], 1000)

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to 
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
            damages.append(damage)
        
        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
