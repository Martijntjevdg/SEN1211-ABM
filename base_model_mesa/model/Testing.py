from functions import calculate_basic_flood_damage, decide_to_adapt, choose_adaptation, calculate_adapted_flood_depth

#Hier komt het liefst de functie: calculate_network_perception()

calculate_basic_flood_damage(3, 60) #Een huis met flood_depth_estimated 2 en 60m2

decide_to_adapt(30000, 3, is_adapted=False)

choose_adaptation(1500, 0, is_adapted = True) #Een household met savings 1500 en nog geen adaptation en wel willen adapten

calculate_adapted_flood_depth(3, 1) #Prints flood_depth according to the adaptation and estimated flood depth

