from model import AdaptationModel
from agents import Households
from functions import calculate_basic_flood_damage

m1 = AdaptationModel(number_of_households=25, flood_map_choice="harvey", network="watts_strogatz")
#all_households = m1.schedule.agents
h1 = m1.all_households[0]
#h1.count_friends(1)
#calculate_basic_flood_damage(h1.flood_depth_estimated, h1.housesize)
print(m1.flood_step)