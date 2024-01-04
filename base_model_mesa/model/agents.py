# Importing necessary libraries
import random

from mesa import Agent
from shapely.geometry import Point
from shapely import contains_xy
from collections import Counter


# Import functions from functions.py
from functions import generate_random_location_within_map_domain, get_flood_depth, calculate_basic_flood_damage, floodplain_multipolygon


# Define the Households agent class
class Households(Agent):
    """
    An agent representing a household in the model.
    Each household has a flood depth attribute which is randomly assigned for demonstration purposes.
    In a real scenario, this would be based on actual geographical data or more complex logic.
    """

    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)
        self.is_adapted = False  # Initial adaptation status set to False
        self.going_to_adapt = False
        self.income_label = self.assign_income_label()
        self.income = self.calculate_income()
        self.savings = 0
        self.housesize = self.assign_housesize()
        self.adaptation_depth = 0
        self.household_damage = 0
        self.optimal_measure = 'None'

        # getting flood map values
        # Get a random location on the map
        loc_x, loc_y = generate_random_location_within_map_domain()
        self.location = Point(loc_x, loc_y)

        # Check whether the location is within floodplain
        self.in_floodplain = False
        if contains_xy(geom=floodplain_multipolygon, x=self.location.x, y=self.location.y):
            self.in_floodplain = True

        # Get the estimated flood depth at those coordinates. 
        # the estimated flood depth is calculated based on the flood map (i.e., past data) so this is not the actual flood depth
        # Flood depth can be negative if the location is at a high elevation
        self.flood_depth_estimated = get_flood_depth(corresponding_map=model.flood_map, location=self.location, band=model.band_flood_img)
        # handle negative values of flood depth
        if self.flood_depth_estimated < 0:
            self.flood_depth_estimated = 0
        
        # calculate the estimated flood damage given the estimated flood depth. Flood damage is a factor between 0 and 1
        # ook in deze regel kunnen we adaptation toevoegen en van de flood_depth_estimated afhalen
        self.flood_damage_estimated = calculate_basic_flood_damage(flood_depth=self.flood_depth_estimated, housesize= self.housesize)

        # Add an attribute for the actual flood depth. This is set to zero at the beginning of the simulation since there is not flood yet
        # and will update its value when there is a shock (i.e., actual flood). Shock happens at some point during the simulation
        self.flood_depth_actual = 0
        #calculate the actual flood damage given the actual flood depth. Flood damage is a factor between 0 and 1
        #In deze regel zouden we de adaptation van de actual flood depth af kunnen halen om te kijken hoeveel damage er is
        self.flood_damage_actual = calculate_basic_flood_damage(flood_depth=self.flood_depth_actual, housesize = self.housesize)

        # Base the initial flood perception on whether the household is in a floodplain or not
        self.own_flood_perception = self.initial_own_flood_perception()
        self.network_flood_perception = 0

    # Function to count friends who can be influential.
    # def count_friends(self, radius):
    #     """Count the number of neighbors within a given radius (number of edges away). This is social relation and not spatial"""
    #     friends = self.model.grid.get_neighborhood(self.pos, include_center=False, radius=radius)
    #     print(friends)
    #     return len(friends)
    def assign_income_label(self):
        # Define the distribution of labels and their probabilities
        income_label_distribution = {'Poor': 25.68, 'Middle-Class': 63.76, 'Rich': 10.55}

        # Randomly choose a label based on the distribution
        rand_num = random.uniform(0, 100)
        cumulative_prob = 0

        for income_label, prob in income_label_distribution.items():
            cumulative_prob += prob
            if rand_num <= cumulative_prob:
                return income_label
    def initial_own_flood_perception(self):
        if self.in_floodplain:
            # Values to choose from
            options = [1, 2, 3, 4]

            # Probabilities for each option (summing to 1)
            probabilities = [0.15, 0.25, 0.3, 0.3]

            # Assign a value based on chance
            flood_perception = random.choices(options, probabilities)[0]
        else:
            flood_perception = random.randint(1, 4)

        return flood_perception
    def calculate_income(self):
        income_distribution = {'Poor': [5000, 1875], 'Middle-Class': [29375, 10312], 'Rich': [87500, 18750]}
        #income_distribution = 'Label': [mean, standard_deviation]
        #Income is per tick which is quarter of a year

        income = round(random.normalvariate(income_distribution[self.income_label][0],
                                            income_distribution[self.income_label][1]))
        return income
    def check(self):
        print(self.flood_damage_estimated)
        print(self.income)
    def assign_housesize(self):
        average_household_surfaces = {'Poor': [100, 30], 'Middle-Class': [201.6, 50], 'Rich': [500, 200]}

        household_size = round(random.normalvariate(average_household_surfaces[self.income_label][0],
                                                 average_household_surfaces[self.income_label][1]))
        return household_size
    def calculate_network_flood_perception(self, all_households):
        radius = 1 #Change this variable to a different radius to change the dynamic of choosing friends
        friends = self.model.grid.get_neighborhood(self.pos, include_center=False, radius=radius)

        network = {}
        for friend in friends:
            network[all_households[friend].unique_id] = all_households[friend].own_flood_perception

        value_counts = Counter(network.values())
        most_common_value, count = value_counts.most_common(1)[0]
        self.network_flood_perception = most_common_value

    def change_own_flood_perception(self):
        # These variables are random integers between 1 and 3 at the moment
        if self.network_flood_perception != self.own_flood_perception:
            self.own_flood_perception = self.network_flood_perception
        return self.own_flood_perception
    def income_to_savings(self):
        self.savings += 0.1*self.income

    def decide_to_adapt(self):
        if self.own_flood_perception == 2:
            if self.flood_depth_estimated > 1.5:
                self.optimal_measure = 'Sandbags'
            else:
                self.optimal_measure = 'None'


        if self.own_flood_perception == 3 and 0.5 < self.flood_depth_estimated < 1.5:
            self.optimal_measure = 'Sandbags'

        if self.own_flood_perception == 3 and 1.5 < self.flood_depth_estimated < 3.5:
            self.optimal_measure = 'Drains'

        if self.own_flood_perception == 3 and self.flood_depth_estimated > 3.5:
            self.optimal_measure = 'Heightening'

        if self.own_flood_perception == 4 and 0.2 < self.flood_depth_estimated < 0.7:
            self.optimal_measure = 'Sandbags'

        if self.own_flood_perception == 4 and 0.7 < self.flood_depth_estimated < 2.5:
            self.optimal_measure = 'Drains'

        if self.own_flood_perception == 4 and self.flood_depth_estimated > 2.5:
            self.optimal_measure = 'Heightening'

    def choose_adaptation(self):
        adaptation_measures = {'Sandbags': [0.5, 5], 'Drains': [1, 30], 'Heightening': [3, 585]}
        # {'Measure': [adaptation_depth, costs per m2]}
        # Assumptions and calculations on costs in Appendix ...

        if self.optimal_measure == 'None':
            # If the agent has not decided to adapt, this function will end here.
            return

        else:
            if (self.savings / self.housesize) >= adaptation_measures[self.optimal_measure][1]:
                self.adaptation_depth = adaptation_measures[self.optimal_measure][0]
                self.savings -= adaptation_measures[self.optimal_measure][1]*self.housesize
            return
        # else:
        #     # For every income_label, there is a different percentage of spendable income
        #     # The choice for this is elaborated in section ... of the report
        #     if self.income_label == 'Poor':
        #         # Spendable income is calculated as a percentage of yearly income (4 ticks) per m2
        #         # This spendable_income is later used to decide whether or not a certain adaptation measure is chosen
        #         spendable_income = (self.income / self.housesize) * 4 * 0.10
        #         # This if sequence kicks off the decision making process
        #         # The assumption is that agents always decide to go for the highest number of adaptation_depth if they can afford it
        #         # So, the agent first checks if it has enough spendable income for the best adaptation measure, heightening.
        #         if spendable_income >= adaptation_measures['Heightening'][1]:
        #             self.adaptation_depth = adaptation_measures['Heightening'][0]
        #             self.is_adapted = True
        #             return self.adaptation_depth
        #         # If they do not have enough spendable income, they check if they have enough to unplug the drains
        #         elif spendable_income >= adaptation_measures['Drains'][1]:
        #             self.adaptation_depth = adaptation_measures['Drains'][0]
        #             self.is_adapted = True
        #             return self.adaptation_depth
        #         # If they do not have enough spendable income again, they check if they have enough to place sandbags
        #         elif spendable_income >= adaptation_measures['Sandbags'][1]:
        #             self.adaptation_depth = adaptation_measures['Sandbags'][0]
        #             self.is_adapted = True
        #             return self.adaptation_depth
        #         # When they have no money for any adaptation measure, adaptation_depth remains the initial value of 0
        #         else:
        #             return self.adaptation_depth
        #
        #     # The same structure as elaborated in comments above, is also used for the other two income_labels
        #     # Note that the percentage used to calculate the spendable income differs between the income_labels
        #     if self.income_label == 'Middle-Class':  # Option 1: place sandbags to reduce flood_depth with half a meter
        #         spendable_income = (self.income / self.housesize) * 4 * 0.25
        #         if spendable_income >= adaptation_measures['Heightening'][1]:
        #             self.adaptation_depth = adaptation_measures['Heightening'][0]
        #             self.is_adapted = True
        #             return self.adaptation_depth
        #         elif spendable_income >= adaptation_measures['Drains'][1]:
        #             self.adaptation_depth = adaptation_measures['Drains'][0]
        #             self.is_adapted = True
        #             return self.adaptation_depth
        #         elif spendable_income >= adaptation_measures['Sandbags'][1]:
        #             self.adaptation_depth = adaptation_measures['Sandbags'][0]
        #             self.is_adapted = True
        #             return self.adaptation_depth
        #         else:
        #             return self.adaptation_depth
        #
        #     if self.income_label == 'Rich':
        #         spendable_income = (self.income / self.housesize) * 4 * 0.50
        #         if spendable_income >= adaptation_measures['Heightening'][1]:
        #             self.adaptation_depth = adaptation_measures['Heightening'][0]
        #             self.is_adapted = True
        #             return self.adaptation_depth
        #         elif spendable_income >= adaptation_measures['Drains'][1]:
        #             self.adaptation_depth = adaptation_measures['Drains'][0]
        #             self.is_adapted = True
        #             return self.adaptation_depth
        #         elif spendable_income >= adaptation_measures['Sandbags'][1]:
        #             self.adaptation_depth = adaptation_measures['Sandbags'][0]
        #             self.is_adapted = True
        #             return self.adaptation_depth
        #         else:
        #             return self.adaptation_depth

    def calculate_adapted_flood_depth_and_damage(self):
        self.flood_depth_estimated = self.flood_depth_estimated - self.adaptation_depth
        self.flood_damage_estimated = calculate_basic_flood_damage(self.flood_depth_estimated, self.housesize)
        return self.flood_depth_estimated

    def step(self):
        # Logic for adaptation based on estimated flood damage and a random chance.
        self.income_to_savings()
        self.calculate_network_flood_perception(self.model.all_households)
        self.change_own_flood_perception()
        self.decide_to_adapt()
        self.choose_adaptation()
        self.calculate_adapted_flood_depth_and_damage()
        
# Define the Government agent class
class Government(Agent):
    """
    A government agent that currently doesn't perform any actions.
    """
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)

    def step(self):
        # The government agent doesn't perform any actions.
        pass

# More agent classes can be added here, e.g. for insurance agents.
