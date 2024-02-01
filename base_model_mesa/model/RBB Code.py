from collections import Counter
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