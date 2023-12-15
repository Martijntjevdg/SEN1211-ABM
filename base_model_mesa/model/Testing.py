from functions import (calculate_basic_flood_damage, decide_to_adapt, choose_adaptation, calculate_adapted_flood_depth,
                       change_own_flood_perception, calculate_optimal_adaptation_measure)

#Hier komt het liefst de functie: calculate_network_perception()

change_own_flood_perception(2,1)

calculate_basic_flood_damage(2, 60) #Een huis met flood_depth_estimated 2 en 60m2

decide_to_adapt(30000, 3, 1, going_to_adapt=False)

choose_adaptation(1500, 0, going_to_adapt = True) #Een household met savings 1500 en nog geen adaptation en wel willen adapten

calculate_adapted_flood_depth(3, 1) #Prints flood_depth according to the adaptation and estimated flood depth

calculate_optimal_adaptation_measure(200, 20, 'Sandbags')
