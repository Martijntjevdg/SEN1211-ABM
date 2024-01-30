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
        """Assigns an income label to an agent based on the income label distribution which represents the real distribution"""
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
        """"Creates an initial own flood perception, a little influenced by whether the household is in a floodplain or not"""
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
        """Calculates the agent income based on income label and the income distribution provided by the model"""
        income = 0
        income_distribution = self.model.income_distribution
        #income_distribution = 'Label': [mean, standard_deviation]
        #Income is per tick which is quarter of a year
        while income <= 0:
            income = round(self.random.normalvariate(income_distribution[self.income_label][0],
                                                income_distribution[self.income_label][1]))
        return income

    def assign_housesize(self):
        """Assigns the housesize of every household based on their income label and the house distribution in the model"""
        household_size = 0
        average_household_surfaces = self.model.average_household_surfaces
        while household_size < 30:
            household_size = round(self.random.normalvariate(average_household_surfaces[self.income_label][0],
                                                 average_household_surfaces[self.income_label][1]))
        return household_size

    def assign_adaptation_measures(self):
        """Assign the adaptation measures options for that specific household. Depending on the subsidies package
        specified in the model, some households receive different options e.g. based on income or location. This
        will later on influence their decision to take adaptation measures or not"""
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
        """This function calculates the flood perception that is most frequently present among the friends of the household
        which will influence their own flood perception via another function"""
        radius = 1 #Change this variable to a different radius to change the dynamic of choosing friends
        friends = self.model.grid.get_neighborhood(self.pos, include_center=False, radius=radius)

        #To access the households in the network better, they are appended to a dictionary with their keys and flood perception
        network = {}
        for friend in friends:
            network[all_households[friend].unique_id] = all_households[friend].own_flood_perception

        self.network = network
        #This counts the number of values in the network
        value_counts = Counter(network.values())
        if len(value_counts) > 0: #If the household has no friends, no error will occur
            most_common_value, count = value_counts.most_common(1)[0] #The most common value is saved a the network flood perception
            self.network_flood_perception = most_common_value
        else:
            self.network_flood_perception = None


    def change_own_flood_perception(self):
        """This simple function is the next step in changing the households perceptions on floods
        If the household has a different opinion than their network, they will adapt to their network flood perception"""
        # These variables are random integers between 1 and 4
        if self.network_flood_perception != self.own_flood_perception and self.network_flood_perception is not None:
            self.own_flood_perception = self.network_flood_perception
        return self.own_flood_perception

    def decide_on_optimal_adaptation(self):
        """This function decides which adaption measure is most optimal for that specific household. This greatly depends on
         location, income and subsidies package."""
        if self.is_adapted == True: #If the household has already adapted, it does not need to go through this process again
            return

        #The margins for every adaptation measure are calculated
        #Margins are defined as the damage with initial flood depth minus the damage with adapted flood depth, which effectively
        #shows how much the households could save with that adaptation measure
        margin_of_sandbags = (self.flood_damage_estimated -
                              calculate_basic_flood_damage((self.flood_depth_estimated-self.adaptation_measures['Sandbags'][0]), self.housesize))

        margin_of_drains = (self.flood_damage_estimated -
                              calculate_basic_flood_damage((self.flood_depth_estimated -self.adaptation_measures['Drains'][0]), self.housesize))

        margin_of_heightening = (self.flood_damage_estimated -
                              calculate_basic_flood_damage((self.flood_depth_estimated -self.adaptation_measures['Heightening'][0]), self.housesize))

        #The costs for each adaptation measure are calculated to see if they are greater or smaller than the margin
        #The cost is the cost (which depends on subsidies package received by the household) per m2 multiplied by the housesize
        costs_for_sandbags = self.adaptation_measures['Sandbags'][1]*self.housesize
        costs_for_drains = self.adaptation_measures['Drains'][1]*self.housesize
        costs_for_heightening = self.adaptation_measures['Heightening'][1]*self.housesize

        #Depending on the flood perception of the household, it will choose to adapt to floods
        #However, someone with percepts a minor risk to floods shall never heighten their house, therefore is not able to via this code
        #The ones with more risk averse flood perception will only choose a certain adaptation measure if the costs outpay the margin
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
        """This function takes the income every step saves it up for the household"""
        #A person with flood_perception 4 saves 10% of their income (do we want to randomize that 10%?)
        if self.going_to_adapt == True:
            self.savings += (self.own_flood_perception/4)*0.10*self.income

    def execute_adaptation(self):
        """This function executes the optimal adaptation if the household is able to"""
        if self.optimal_measure == 'None' or self.is_adapted == True:
            # If the agent has not decided to adapt, this function will end here.
            return

        else:
            #If the household has decided to adapt and can their savings are high enough to pay for the adaptation measure
            #The household will adapt to flood accordingly
            if (self.savings / self.housesize) >= self.adaptation_measures[self.optimal_measure][1] and self.going_to_adapt == True:
                #The given height that is lessened by taking that adaptation measure
                self.adaptation_depth = self.adaptation_measures[self.optimal_measure][0]
                #Show that the houhsehold has "paid" by substracting the number from savings
                self.savings -= self.adaptation_measures[self.optimal_measure][1]*self.housesize
                #The number that was substracted previously shown as the cost for adaptation
                self.cost_of_adaptation = self.adaptation_measures[self.optimal_measure][1]*self.housesize
                #The difference in what they would originally pay for the measure and have paid to show how much the subsidies cost
                self.subsidies_received = calculate_subsidies_received(self.optimal_measure, self.cost_of_adaptation, self.housesize)
                #Change the flood_depth to fully install the flood depth
                self.flood_depth_estimated = self.flood_depth_estimated - self.adaptation_depth
                #It is not possible to get a negative flood depth
                if self.flood_depth_estimated < 0:
                    self.flood_depth_estimated = 0
                #Calculate the new estimated flood damage with the adapted flood depth
                self.flood_damage_estimated = calculate_basic_flood_damage(self.flood_depth_estimated, self.housesize)
                #Switch of that they are going to adapt
                self.going_to_adapt = False
                #Save the measure they have installed
                self.optimal_measure = str(self.optimal_measure) + '_' + str(self.model.schedule.steps)
                #Show that they have adapted
                self.is_adapted = True
            return

    def step(self):
        # Logic for adaptation based on estimated flood damage and a random chance.
        self.calculate_network_flood_perception(self.model.all_households)
        self.change_own_flood_perception()
        self.decide_on_optimal_adaptation()
        self.save_income()
        self.execute_adaptation()

