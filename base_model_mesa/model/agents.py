# Importing necessary libraries
import random

from mesa import Agent
from shapely.geometry import Point
from shapely import contains_xy
from collections import Counter


# Import functions from functions.py
from functions import generate_random_location_within_map_domain, get_flood_depth, calculate_basic_flood_damage, floodplain_multipolygon, calculate_subsidies_received


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
        self.going_to_adapt = False #Flicks to True when a Household decides to adapt and flicks back when the adaptation is completed
        self.income_label = self.assign_income_label() #Household receives an income label: 'Poor', 'Middle-Class', 'Rich'
        self.income = self.calculate_income() #Income per step is calculated based on income label
        self.savings = 0 #Savings start at 0 for every household, a part of income is saved each step
        self.housesize = self.assign_housesize() #Based on income label, a household is assigned a certain house size in m2
        self.adaptation_depth = 0 #Initial adaptation depth is 0 as Household have no adaptation at initialization
        self.cost_of_adaptation = 0 #Initial cost of adaptation is 0 as Households have no adaptation at initialization
        self.subsidies_received = 0 #Initial subsidies received is 0 when Households have not managed to do adaptation yet
        self.optimal_measure = 'None' #Initial optimal measure is None, is assigned from the first step and can change over time
        # getting flood map values
        # Get a random location on the map
        loc_x, loc_y = generate_random_location_within_map_domain(model)
        self.location = Point(loc_x, loc_y)

        #For verification purposes, the network of the agent is collected in the following variable
        self.network = {}

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
        self.flood_damage_estimated = calculate_basic_flood_damage(flood_depth=self.flood_depth_estimated, housesize= self.housesize)

        # Add an attribute for the actual flood depth. This is set to zero at the beginning of the simulation since there is not flood yet
        # and will update its value when there is a shock (i.e., actual flood). Shock happens at some point during the simulation
        self.flood_depth_actual = 0
        #calculate the actual flood damage given the actual flood depth. Flood damage is a factor between 0 and 1
        self.flood_damage_actual = calculate_basic_flood_damage(flood_depth=self.flood_depth_actual, housesize = self.housesize)

        # Base the initial flood perception on whether the household is in a floodplain or not
        self.own_flood_perception = self.initial_own_flood_perception()
        #The perception within the network is calculated in step 1, so initially set to 0
        self.network_flood_perception = 0

        self.adaptation_measures = self.assign_adaptation_measures()

    def assign_income_label(self):
        # Define the distribution of labels and their probabilities
        income_label_distribution = {'Poor': 25.68, 'Middle-Class': 63.76, 'Rich': 10.55}

        # Randomly choose a label based on the distribution
        while True:
            # Randomly choose a label based on the distribution
            rand_num = self.random.uniform(0, 100)
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
            flood_perception = self.random.choices(options, probabilities)[0]
        else:
            flood_perception = self.random.randint(1, 4)

        return flood_perception
    def calculate_income(self):
        income = 0
        income_distribution = self.model.income_distribution
        #income_distribution = 'Label': [mean, standard_deviation]
        #Income is per tick which is quarter of a year
        while income <= 0:
            income = round(self.random.normalvariate(income_distribution[self.income_label][0],
                                                income_distribution[self.income_label][1]))
        return income

    def assign_housesize(self):
        household_size = 0
        average_household_surfaces = self.model.average_household_surfaces
        while household_size < 30:
            household_size = round(self.random.normalvariate(average_household_surfaces[self.income_label][0],
                                                 average_household_surfaces[self.income_label][1]))
        return household_size

    def assign_adaptation_measures(self):
        if self.model.subsidies_package == 0:
            adaptation_measures = {'Sandbags': [0.2, 5], 'Drains': [0.7, 30], 'Heightening': [2.5, 585]}

        if self.model.subsidies_package == 1:
            adaptation_measures = {'Sandbags': [0.2, 3], 'Drains': [0.7, 20], 'Heightening': [2.5, 300]}

        if self.model.subsidies_package == 2:
            if self.income_label == 'Poor':
                adaptation_measures = {'Sandbags': [0.2, 2], 'Drains': [0.7, 15], 'Heightening': [2.5, 150]}

            if self.income_label == 'Middle-Class':
                adaptation_measures = {'Sandbags': [0.2, 3], 'Drains': [0.7, 20], 'Heightening': [2.5, 300]}

            if self.income_label == 'Rich':
                adaptation_measures = {'Sandbags': [0.2, 5], 'Drains': [0.7, 30], 'Heightening': [2.5, 585]}

        if self.model.subsidies_package == 3:
            if self.flood_depth_estimated <= 1:
                adaptation_measures = {'Sandbags': [0.2, 5], 'Drains': [0.7, 30], 'Heightening': [2.5, 585]}

            if 1 < self.flood_depth_estimated <= 2:
                adaptation_measures = {'Sandbags': [0.2, 3], 'Drains': [0.7, 20], 'Heightening': [2.5, 300]}

            if self.flood_depth_estimated > 2:
                adaptation_measures = {'Sandbags': [0.2, 2], 'Drains': [0.7, 15], 'Heightening': [2.5, 150]}

        return adaptation_measures
    def calculate_network_flood_perception(self, all_households):
        radius = 1 #Change this variable to a different radius to change the dynamic of choosing friends
        friends = self.model.grid.get_neighborhood(self.pos, include_center=False, radius=radius)

        network = {}
        for friend in friends:
            network[all_households[friend].unique_id] = all_households[friend].own_flood_perception

        self.network = network
        value_counts = Counter(network.values())
        most_common_value, count = value_counts.most_common(1)[0]
        self.network_flood_perception = most_common_value

    def change_own_flood_perception(self):
        # These variables are random integers between 1 and 4 at the moment
        if self.network_flood_perception != self.own_flood_perception:
            self.own_flood_perception = self.network_flood_perception
        return self.own_flood_perception

    def decide_on_optimal_adaptation(self):
        if self.is_adapted == True:
            return

        margin_of_sandbags = (self.flood_damage_estimated -
                              calculate_basic_flood_damage((self.flood_depth_estimated-self.adaptation_measures['Sandbags'][0]), self.housesize))

        margin_of_drains = (self.flood_damage_estimated -
                              calculate_basic_flood_damage((self.flood_depth_estimated -self.adaptation_measures['Drains'][0]), self.housesize))

        margin_of_heightening = (self.flood_damage_estimated -
                              calculate_basic_flood_damage((self.flood_depth_estimated -self.adaptation_measures['Heightening'][0]), self.housesize))

        costs_for_sandbags = self.adaptation_measures['Sandbags'][1]*self.housesize
        costs_for_drains = self.adaptation_measures['Drains'][1]*self.housesize
        costs_for_heightening = self.adaptation_measures['Heightening'][1]*self.housesize

        if self.own_flood_perception == 2 and margin_of_sandbags > costs_for_sandbags:
            self.optimal_measure = 'Sandbags'
            self.going_to_adapt = True

        if self.own_flood_perception == 3 and margin_of_sandbags > costs_for_sandbags:
            self.optimal_measure = 'Sandbags'
            self.going_to_adapt = True

        if self.own_flood_perception == 3 and margin_of_drains > costs_for_drains:
            self.optimal_measure = 'Drains'
            self.going_to_adapt = True

        if self.own_flood_perception == 3 and margin_of_heightening > costs_for_heightening:
            self.optimal_measure = 'Heightening'
            self.going_to_adapt = True

        if self.own_flood_perception == 4 and margin_of_sandbags > costs_for_sandbags:
            self.optimal_measure = 'Sandbags'
            self.going_to_adapt = True

        if self.own_flood_perception == 4 and margin_of_drains > costs_for_drains:
            self.optimal_measure = 'Drains'
            self.going_to_adapt = True

        if self.own_flood_perception == 4 and margin_of_heightening > costs_for_heightening:
            self.optimal_measure = 'Heightening'
            self.going_to_adapt = True
    def save_income(self):
        #A person with flood_perception 4 saves 10% of their income (do we want to randomize that 10%?)
        if self.going_to_adapt == True:
            self.savings += (self.own_flood_perception/4)*0.10*self.income

    def execute_adaptation(self):
        if self.optimal_measure == 'None' or self.is_adapted == True:
            # If the agent has not decided to adapt, this function will end here.
            return

        else:
            if (self.savings / self.housesize) >= self.adaptation_measures[self.optimal_measure][1] and self.going_to_adapt == True:
                self.adaptation_depth = self.adaptation_measures[self.optimal_measure][0]
                self.savings -= self.adaptation_measures[self.optimal_measure][1]*self.housesize
                self.cost_of_adaptation = self.adaptation_measures[self.optimal_measure][1]*self.housesize
                self.subsidies_received = calculate_subsidies_received(self.optimal_measure, self.cost_of_adaptation, self.housesize)
                self.flood_depth_estimated = self.flood_depth_estimated - self.adaptation_depth
                if self.flood_depth_estimated < 0:
                    self.flood_depth_estimated = 0
                self.flood_damage_estimated = calculate_basic_flood_damage(self.flood_depth_estimated, self.housesize)
                self.going_to_adapt = False
                self.optimal_measure = str(self.optimal_measure) + '_' + str(self.model.schedule.steps)
                self.is_adapted = True
            return

    def step(self):
        # Logic for adaptation based on estimated flood damage and a random chance.
        self.calculate_network_flood_perception(self.model.all_households)
        self.change_own_flood_perception()
        self.decide_on_optimal_adaptation()
        self.save_income()
        self.execute_adaptation()

