from model import AdaptationModel
from agents import Households

m1 = AdaptationModel(number_of_households=25, flood_map_choice="harvey", network="watts_strogatz")
all_households = m1.schedule.agents
h1 = all_households[0]
#h1.count_friends(1)

h1.calculate_network_flood_perception(1, all_households)