# -*- coding: utf-8 -*-
"""
@author: thoridwagenblast

Functions that are used in the model_file.py and agent.py for the running of the Flood Adaptation Model.
Functions get called by the Model and Agent class.
"""
import random
import numpy as np
import math
from shapely import contains_xy
from shapely import prepare
import geopandas as gpd
import os


def set_initial_values(input_data, parameter, seed):
    """
    Function to set the values based on the distribution shown in the input data for each parameter.
    The input data contains which percentage of households has a certain initial value.
    
    Parameters
    ----------
    input_data: the dataframe containing the distribution of parameters
    parameter: parameter name that is to be set
    seed: agent's seed
    
    Returns
    -------
    parameter_set: the value that is set for a certain agent for the specified parameter 
    """
    parameter_set = 0
    parameter_data = input_data.loc[
        (input_data.parameter == parameter)]  # get the distribution of values for the specified parameter
    parameter_data = parameter_data.reset_index()
    random.seed(seed)
    random_parameter = random.randint(0, 100)
    for i in range(len(parameter_data)):
        if i == 0:
            if random_parameter < parameter_data['value_for_input'][i]:
                parameter_set = parameter_data['value'][i]
                break
        else:
            if (random_parameter >= parameter_data['value_for_input'][i - 1]) and (
                    random_parameter <= parameter_data['value_for_input'][i]):
                parameter_set = parameter_data['value'][i]
                break
            else:
                continue
    return parameter_set


def get_flood_map_data(flood_map):
    """
    Getting the flood map characteristics.
    
    Parameters
    ----------
    flood_map: flood map in tif format

    Returns
    -------
    band, bound_l, bound_r, bound_t, bound_b: characteristics of the tif-file
    """
    band = flood_map.read(1)
    bound_l = flood_map.bounds.left
    bound_r = flood_map.bounds.right
    bound_t = flood_map.bounds.top
    bound_b = flood_map.bounds.bottom
    return band, bound_l, bound_r, bound_t, bound_b


shapefile_path = r'../input_data/model_domain/houston_model/houston_model.shp'
floodplain_path = r'../input_data/floodplain/floodplain_area.shp'

# Model area setup
map_domain_gdf = gpd.GeoDataFrame.from_file(shapefile_path)
map_domain_gdf = map_domain_gdf.to_crs(epsg=26915)
map_domain_geoseries = map_domain_gdf['geometry']
map_minx, map_miny, map_maxx, map_maxy = map_domain_geoseries.total_bounds
map_domain_polygon = map_domain_geoseries[0]  # The geoseries contains only one polygon
prepare(map_domain_polygon)

# Floodplain setup
floodplain_gdf = gpd.GeoDataFrame.from_file(floodplain_path)
floodplain_gdf = floodplain_gdf.to_crs(epsg=26915)
floodplain_geoseries = floodplain_gdf['geometry']
floodplain_multipolygon = floodplain_geoseries[0]  # The geoseries contains only one multipolygon
prepare(floodplain_multipolygon)


def generate_random_location_within_map_domain():
    """
    Generate random location coordinates within the map domain polygon.

    Returns
    -------
    x, y: lists of location coordinates, longitude and latitude
    """
    while True:
        # generate random location coordinates within square area of map domain
        x = random.uniform(map_minx, map_maxx)
        y = random.uniform(map_miny, map_maxy)
        # check if the point is within the polygon, if so, return the coordinates
        if contains_xy(map_domain_polygon, x, y):
            return x, y


def get_flood_depth(corresponding_map, location, band):
    """ 
    To get the flood depth of a specific location within the model domain.
    Households are placed randomly on the map, so the distribution does not follow reality.
    
    Parameters
    ----------
    corresponding_map: flood map used
    location: household location (a Shapely Point) on the map
    band: band from the flood map

    Returns
    -------
    depth: flood depth at the given location
    """
    row, col = corresponding_map.index(location.x, location.y)
    depth = band[row - 1, col - 1]
    return depth

def get_position_flood(bound_l, bound_r, bound_t, bound_b, img, seed):
    """ 
    To generater the position on flood map for a household.
    Households are placed randomly on the map, so the distribution does not follow reality.
    
    Parameters
    ----------
    bound_l, bound_r, bound_t, bound_b, img: characteristics of the flood map data (.tif file)
    seed: seed to generate the location on the map

    Returns
    -------
    x, y: location on the map
    row, col: location within the tif-file
    """
    random.seed(seed)
    x = random.randint(round(bound_l, 0), round(bound_r, 0))
    y = random.randint(round(bound_b, 0), round(bound_t, 0))
    row, col = img.index(x, y)
    return x, y, row, col


def calculate_basic_flood_damage(flood_depth, housesize):
    """
    To get flood damage based on flood depth of household
    from de Moer, Huizinga (2017) with logarithmic regression over it.
    If flood depth > 6m, damage = 1.
    
    Parameters
    ----------
    flood_depth : flood depth as given by location within model domain

    Returns
    -------
    flood_damage : damage factor between 0 and 1
    """
    # Multiply flood_damage with average price in euro's per m2. Housesize is per agent in m2, to make sure
    if flood_depth >= 6:
        flood_damage = 1 * 788 * housesize
    elif flood_depth < 0.025:
        flood_damage = 0
    else:
        # see flood_damage.xlsx for function generation
        flood_damage = (0.1746 * math.log(flood_depth) + 0.6483) * 788 * housesize
    #print(flood_damage)
    return flood_damage

def calculate_network_flood_perception():
    #Er wordt een variabele friends aangemaakt in de functie count_friends
    #Kan ik hier het berekenen van de network_perception aan toevoegen?
    #Waarschijnlijk is het een list aan friends waar je vervolgens de network_perception van kan opvragen
    #Maar het lukt me niet om dat nu te controleren omdat ik moeite heb code te runnen in Pycharm

    #Two options for output: one variable that is decided on the highest number present
    #Or: dictionary that counts every value in the network, to change you take the highest value in the dictionary

    return

def change_own_flood_perception(own_flood_perception, network_flood_perception):
    #These variables are random integers between 1 and 3 at the moment
    if network_flood_perception != own_flood_perception:
        own_flood_perception = network_flood_perception
    #print(own_flood_perception)
    return own_flood_perception


def decide_to_adapt(flood_damage_estimated, own_flood_perception, adaptation_depth, going_to_adapt):
    if adaptation_depth != 0:
        going_to_adapt = False
        return going_to_adapt

    if flood_damage_estimated > 95000 and own_flood_perception == 3:
        going_to_adapt = True
    #print(going_to_adapt)
    return going_to_adapt



#De functie hieronder kunnen we uitbouwen onderbouwd met een diagram die de keuze van een household weergeeft
#Mag alles zijn: savings threshold, housesize, perception, alles kan er in gestopt worden
#Maar hier kan ik de wiskunde laten kloppen en testen met Testing.py
def choose_adaptation(income, housesize, income_label, going_to_adapt, adaptation_depth, is_adapted = False):
    adaptation_measures = {'Sandbags': [0.5, 5], 'Drains': [1, 30], 'Heightening': [3, 585]}
    #{'Measure': [adaptation_depth, costs per m2]}
    #Assumptions and calculations on costs in Appendix ...

    if going_to_adapt == False:
        #If the agent has not decided to adapt, this function will end here.
        return
    else:
        #For every income_label, there is a different percentage of spendable income
        #The choice for this is elaborated in section ... of the report
        if income_label == 'Poor':
            #Spendable income is calculated as a percentage of yearly income (4 ticks) per m2
            #This spendable_income is later used to decide whether or not a certain adaptation measure is chosen
            spendable_income = (income/housesize)*4*0.10
            #print(spendable_income)
            #This if sequence kicks off the decision making process
            #The assumption is that agents always decide to go for the highest number of adaptation_depth if they can afford it
            #So, the agent first checks if it has enough spendable income for the best adaptation measure, heightening.
            if spendable_income >= adaptation_measures['Heightening'][1]:
                adaptation_depth = adaptation_measures['Heightening'][0]
                is_adapted = True
                #print(adaptation_depth)
                return adaptation_depth
            #If they do not have enough spendable income, they check if they have enough to unplug the drains
            elif spendable_income >= adaptation_measures['Drains'][1]:
                adaptation_depth = adaptation_measures['Drains'][0]
                is_adapted = True
                #print(adaptation_depth)
                return adaptation_depth
            #If they do not have enough spendable income again, they check if they have enough to place sandbags
            elif spendable_income >= adaptation_measures['Sandbags'][1]:
                adaptation_depth = adaptation_measures['Sandbags'][0]
                is_adapted = True
                #print(adaptation_depth)
                return adaptation_depth
            #When they have no money for any adaptation measure, adaptation_depth remains the initial value of 0
            else:
                return adaptation_depth

        #The same structure as elaborated in comments above, is also used for the other two income_labels
        #Note that the percentage used to calculate the spendable income differs between the income_labels
        if income_label == 'Middle-Class': #Option 1: place sandbags to reduce flood_depth with half a meter
            spendable_income = (income/housesize)*4*0.25
            #print(spendable_income)
            if spendable_income >= adaptation_measures['Heightening'][1]:
                adaptation_depth = adaptation_measures['Heightening'][0]
                is_adapted = True
                #print(adaptation_depth)
                return adaptation_depth
            elif spendable_income >= adaptation_measures['Drains'][1]:
                adaptation_depth = adaptation_measures['Drains'][0]
                is_adapted = True
                #print(adaptation_depth)
                return adaptation_depth
            elif spendable_income >= adaptation_measures['Sandbags'][1]:
                adaptation_depth = adaptation_measures['Sandbags'][0]
                is_adapted = True
                #print(adaptation_depth)
                return adaptation_depth
            else:
                #print(adaptation_depth)
                return adaptation_depth

        if income_label == 'Rich':
            spendable_income = (income/housesize)*4*0.50
            #print(spendable_income)
            if spendable_income >= adaptation_measures['Heightening'][1]:
                adaptation_depth = adaptation_measures['Heightening'][0]
                is_adapted = True
                #print(adaptation_depth)
                return adaptation_depth
            elif spendable_income >= adaptation_measures['Drains'][1]:
                adaptation_depth = adaptation_measures['Drains'][0]
                is_adapted = True
                #print(adaptation_depth)
                return adaptation_depth
            elif spendable_income >= adaptation_measures['Sandbags'][1]:
                adaptation_depth = adaptation_measures['Sandbags'][0]
                is_adapted = True
                #print(adaptation_depth)
                return adaptation_depth
            else:
                #print(adaptation_depth)
                return adaptation_depth

def calculate_adapted_flood_depth(estimated_flood_depth, adaptation_depth):
    estimated_flood_depth = estimated_flood_depth - adaptation_depth
    #print(estimated_flood_depth)
    return estimated_flood_depth