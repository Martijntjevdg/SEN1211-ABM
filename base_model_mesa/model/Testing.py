import random
import numpy as np

from functions import (calculate_basic_flood_damage, decide_to_adapt, choose_adaptation, calculate_adapted_flood_depth)

#Hier komt het liefst de functie: calculate_network_perception()

#change_own_flood_perception(2,1)

#calculate_basic_flood_damage(2, 60) #Een huis met flood_depth_estimated 2 en 60m2

#decide_to_adapt(30000, 3, 1, going_to_adapt=False)

#choose_adaptation(1500, 0, going_to_adapt = True) #Een household met savings 1500 en nog geen adaptation en wel willen adapten

#calculate_adapted_flood_depth(3, 1) #Prints flood_depth according to the adaptation and estimated flood depth

# calculate_optimal_adaptation_measure(200, 20, 'Sandbags')

class Household():
    def __init__(self):
        self.income_label = self.assign_income_label()
        self.income = self.calculate_income()
        self.housesize = self.assign_housesize()
        self.going_to_adapt = True
        self.adaptation_depth = 0

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

    def show_income_label(self):
        print("Income label =", self.income_label)
        print("Income =", self.income)
        print("Housesize =", self.housesize)

    def calculate_income(self):
        income_distribution = {'Poor': [5000, 1875], 'Middle-Class': [29375, 10312], 'Rich': [87500, 18750]}
        #income_distribution = 'Label': [mean, standard_deviation]
        #Income is per tick which is quarter of a year

        income = round(random.normalvariate(income_distribution[self.income_label][0],
                                            income_distribution[self.income_label][1]))
        return income

    def assign_housesize(self):
        average_household_surfaces = {'Poor': [100, 30], 'Middle-Class': [201.6, 50], 'Rich': [500, 200]}

        household_size = round(random.normalvariate(average_household_surfaces[self.income_label][0],
                                                 average_household_surfaces[self.income_label][1]))
        return household_size



h1 = Household()
h1.show_income_label()

choose_adaptation(h1.income, h1.housesize, h1.income_label, h1.going_to_adapt, h1.adaptation_depth, is_adapted=False)

