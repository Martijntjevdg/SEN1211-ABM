# Importing necessary libraries
import networkx as nx
from mesa import Model, Agent
from mesa.time import RandomActivation, BaseScheduler
from mesa.space import NetworkGrid
from mesa.datacollection import DataCollector
import geopandas as gpd
import rasterio as rs
import matplotlib.pyplot as plt
import random

# Import the agent class(es) from agents.py
from agents import Households

# Import functions from functions.py
from functions import get_flood_map_data, calculate_basic_flood_damage
from functions import map_domain_gdf, floodplain_gdf


# Define the AdaptationModel class
class AdaptationModel(Model):
    """
    The main model running the simulation. It sets up the network of household agents,
    simulates their behavior, and collects data. The network type can be adjusted based on study requirements.
    """

    def __init__(self, 
                 seed=None,
                 number_of_households=25, # number of household agents
                 number_of_steps=80, #maximum number of steps (20 years in total, 1 step is quarter year)
                 subsidies_package=0,#decides whether and which subsidies are applied in the model for the household agents
                 #Standard distribution that decides the income for agents with random normal. Income_label:[mean,std_dv]
                 income_distribution={'Poor': [5000, 1875], 'Middle-Class': [29375, 10312], 'Rich': [87500, 18750]},
                 #Standard distribution that decides housesize for agents with random normal. Income_label:[mean, std_dv]
                 average_household_surfaces={'Poor': [100, 30], 'Middle-Class': [201.6, 50], 'Rich': [500, 200]},
                 # Simplified argument for choosing flood map. Can currently be "harvey", "100yr", or "500yr".
                 flood_map_choice='harvey',
                 # ### network related parameters ###
                 # The social network structure that is used.
                 # Can currently be "erdos_renyi", "barabasi_albert", "watts_strogatz", or "no_network"
                 network = 'watts_strogatz',
                 # likeliness of edge being created between two nodes
                 probability_of_network_connection = 0.4,
                 # number of edges for BA network
                 number_of_edges = 3,
                 # number of nearest neighbours for WS social network
                 number_of_nearest_neighbours = 5,
                 ):
        
        super().__init__(seed = seed)
        
        # defining the variables and setting the values
        self.number_of_steps = number_of_steps
        self.subsidies_package = subsidies_package
        self.number_of_households = number_of_households  # Total number of household agents
        self.seed = seed
        self.income_distribution = income_distribution #Can vary based on model parameter input
        self.income_distribution_label = None #Used to store which income_label is used in a model for sensitivity analysis
        self.average_household_surfaces = average_household_surfaces #Can vary based on model parameter input

        #This variable randomly decides when the flood occurs between the parameters given
        self.flood_step = self.random.randint(1, number_of_steps)

        # network
        self.network = network # Type of network to be created
        self.probability_of_network_connection = probability_of_network_connection
        self.number_of_edges = number_of_edges
        self.number_of_nearest_neighbours = number_of_nearest_neighbours

        # generating the graph according to the network used and the network parameters specified
        self.G = self.initialize_network()
        # create grid out of network graph
        self.grid = NetworkGrid(self.G)

        # Initialize maps
        self.initialize_maps(flood_map_choice)

        # set schedule for agents
        self.schedule = BaseScheduler(self)  # Schedule for activating agents

        # create households through initiating a household on each node of the network graph
        for i, node in enumerate(self.G.nodes()):
            household = Households(unique_id=i, model=self)
            self.schedule.add(household)
            self.grid.place_agent(agent=household, node_id=node)

        # The next line creates the all_households variable, which is used to calculate the network_flood_perception
        self.all_households = self.schedule.agents


        # Data collection setup to collect data
        model_metrics = {
                        "TotalAdaptedHouseholds": self.total_adapted_households,
                        "TotalActualDamage": self.total_actual_damage,
                        "TotalExpectedDamage": self.total_expected_damage,
                        "TotalAdaptationCosts":self.total_adaptation_costs,
                        "TotalCostsOfSubsidies":self.total_subsidies_costs,
                        "AverageDamagePerIncomeLabel":self.calculate_damage_per_agent_per_income_label,
                        "EstimatedAverageDamagePerIncomeLabel": self.calculate_estimated_damage_per_agent_per_income_label,
                        "AverageIncomeToDamageRatio":self.calculate_average_income_to_damage_ratio,
                        "EstimatedAverageIncomeToDamageRatio":self.calculate_estimated_average_income_to_damage_ratio,
                        "IncomeDistribution":self.save_income_distribution_label
                        # ... other reporters ...
                        }
        
        agent_metrics = {
                        "FloodDepthEstimated": "flood_depth_estimated",
                        "FloodDamageEstimated" : "flood_damage_estimated",
                        "HouseSize":"housesize",
                        "Location":"location",
                        "FloodDepthActual": "flood_depth_actual",
                        "FloodDamageActual" : "flood_damage_actual",
                        "OptimalMeasure": "optimal_measure",
                        "AdaptationMeasures":"adaptation_measures",
                        "GoingToAdapt":"going_to_adapt",
                        "IsAdapted": "is_adapted",
                        "CostOfAdaptation": "cost_of_adaptation",
                        "IncomeLabel": "income_label",
                        "Income":"income",
                        "Savings":"savings",
                        "OwnFloodPerception":"own_flood_perception",
                        "NetworkPerception":"network_flood_perception",
                        "Network":"network"
                        # ... other reporters ...
                        }
        #set up the data collector 
        self.datacollector = DataCollector(model_reporters=model_metrics)#, agent_reporters=agent_metrics)
            

    def initialize_network(self):
        """
        Initialize and return the social network graph based on the provided network type using pattern matching.
        """
        if self.network == 'erdos_renyi':
            return nx.erdos_renyi_graph(n=self.number_of_households,
                                        p=self.number_of_nearest_neighbours / self.number_of_households,
                                        seed=self.seed)
        elif self.network == 'barabasi_albert':
            return nx.barabasi_albert_graph(n=self.number_of_households,
                                            m=self.number_of_edges,
                                            seed=self.seed)
        elif self.network == 'watts_strogatz':
            return nx.watts_strogatz_graph(n=self.number_of_households,
                                        k=self.number_of_nearest_neighbours,
                                        p=self.probability_of_network_connection,
                                        seed=self.seed)
        elif self.network == 'no_network':
            G = nx.Graph()
            G.add_nodes_from(range(self.number_of_households))
            return G
        else:
            raise ValueError(f"Unknown network type: '{self.network}'. "
                            f"Currently implemented network types are: "
                            f"'erdos_renyi', 'barabasi_albert', 'watts_strogatz', and 'no_network'")


    def initialize_maps(self, flood_map_choice):
        """
        Initialize and set up the flood map related data based on the provided flood map choice.
        """
        # Define paths to flood maps
        flood_map_paths = {
            'harvey': r'../input_data/floodmaps/Harvey_depth_meters.tif',
            '100yr': r'../input_data/floodmaps/100yr_storm_depth_meters.tif',
            '500yr': r'../input_data/floodmaps/500yr_storm_depth_meters.tif'  # Example path for 500yr flood map
        }

        # Throw a ValueError if the flood map choice is not in the dictionary
        if flood_map_choice not in flood_map_paths.keys():
            raise ValueError(f"Unknown flood map choice: '{flood_map_choice}'. "
                             f"Currently implemented choices are: {list(flood_map_paths.keys())}")

        # Choose the appropriate flood map based on the input choice
        flood_map_path = flood_map_paths[flood_map_choice]

        # Loading and setting up the flood map
        self.flood_map = rs.open(flood_map_path)
        self.band_flood_img, self.bound_left, self.bound_right, self.bound_top, self.bound_bottom = get_flood_map_data(
            self.flood_map)


    def save_income_distribution_label(self):
        """
        Function used to save model data.
        Checks what the income_distribution is in the model parameter space and saves the label accordingly
        Mainly used for sensitivity analysis
        """
        if self.income_distribution == {'Poor': [5000, 1875], 'Middle-Class': [29375, 10312], 'Rich': [87500, 18750]}:
            income_distribution_label = 'Base'
        if self.income_distribution == {'Poor': [5500, 1875], 'Middle-Class': [32312.5, 10321], 'Rich': [96250, 18750]}:
            income_distribution_label = 'Plus10'
        if self.income_distribution == {'Poor': [4500, 1875], 'Middle-Class': [26437.5, 10321], 'Rich': [78750, 18750]}:
            income_distribution_label = 'Minus10'
        if self.income_distribution == {'Poor': [6500, 1875], 'Middle-Class': [38187.5, 10321], 'Rich': [133750, 18750]}:
            income_distribution_label = 'Plus30'
        if self.income_distribution == {'Poor': [3500, 1875], 'Middle-Class': [20562.5, 10321], 'Rich': [61250, 18750]}:
            income_distribution_label = 'Minus30'

        return income_distribution_label
    def total_adapted_households(self):
        """Return the total number of households that have adapted."""
        #BE CAREFUL THAT YOU MAY HAVE DIFFERENT AGENT TYPES SO YOU NEED TO FIRST CHECK IF THE AGENT IS ACTUALLY A HOUSEHOLD AGENT USING "ISINSTANCE"
        adapted_count = sum([1 for agent in self.schedule.agents if isinstance(agent, Households) and agent.is_adapted])
        return adapted_count

    def total_actual_damage(self):
        """"Return the total damaged experienced after a flood occured by all agents"""
        total_actual_damage = sum(agent.flood_damage_actual for agent in self.schedule.agents)
        return total_actual_damage

    def total_expected_damage(self):
        """"Return the total expected damage summed for all agents"""
        total_expected_damage = sum(agent.flood_damage_estimated for agent in self.schedule.agents)
        return total_expected_damage

    def total_adaptation_costs(self):
        """"Return the total adaptation costs summed for all agents"""
        total_adaptation_costs = sum(agent.cost_of_adaptation for agent in self.schedule.agents)
        return total_adaptation_costs

    def total_subsidies_costs(self):
        """"Return the total cost of subsidies spent by all agents"""
        total_cost_of_subsidies = sum(agent.subsidies_received for agent in self.schedule.agents)
        return total_cost_of_subsidies

    def calculate_damage_per_agent_per_income_label(self):
        """
        Function to calculate the average damage per income label for the agents
        """
        #Dictionary with the three labels and their respective average damage per agent in that label
        damage_per_agent_per_income_label = {}

        #Create subsets of all the agents within the model based on income_label
        poor_agents = [agent for agent in self.schedule.agents if agent.income_label == 'Poor']
        middle_class_agents = [agent for agent in self.schedule.agents if agent.income_label == 'Middle-Class']
        rich_agents = [agent for agent in self.schedule.agents if agent.income_label == 'Rich']

        #Calculate the total damage per income label for all agents
        total_damage_poor_agents = sum(agent.flood_damage_actual for agent in self.schedule.agents if agent.income_label == 'Poor')
        total_damage_middle_class_agents = sum(agent.flood_damage_actual for agent in self.schedule.agents if agent.income_label == 'Middle-Class')
        total_damage_rich_agents = sum(agent.flood_damage_actual for agent in self.schedule.agents if agent.income_label == 'Rich')

        #Calculate the average damage per agent of income class by dividing it with the number of agents of that income class in the model
        average_damage_per_poor_agent = total_damage_poor_agents/len(poor_agents)
        average_damage_per_middle_class_agent = total_damage_middle_class_agents/len(middle_class_agents)
        if len(rich_agents) > 0:
            average_damage_per_rich_agent = total_damage_rich_agents/len(rich_agents)
        else:
            return 'No Rich Agents in the model'

        #Append the values into the empty dictionary created at the beginning
        damage_per_agent_per_income_label['AverageDamagePerPoorHousehold'] = average_damage_per_poor_agent
        damage_per_agent_per_income_label['AverageDamagePerMiddleClassHousehold'] = average_damage_per_middle_class_agent
        damage_per_agent_per_income_label['AverageDamagePerRichHousehold'] = average_damage_per_rich_agent

        #The values are returned as a dictionary which will later be unpacked after the model has been run
        #This dictionary is unpacked into three seperate columns for each income label
        return damage_per_agent_per_income_label

    def calculate_estimated_damage_per_agent_per_income_label(self):
        """
        Function to calculate the average damage per income label for the agents
        """
        #Dictionary with the three labels and their respective average damage per agent in that label
        damage_per_agent_per_income_label = {}

        #Create subsets of all the agents within the model based on income_label
        poor_agents = [agent for agent in self.schedule.agents if agent.income_label == 'Poor']
        middle_class_agents = [agent for agent in self.schedule.agents if agent.income_label == 'Middle-Class']
        rich_agents = [agent for agent in self.schedule.agents if agent.income_label == 'Rich']

        #Calculate the total damage per income label for all agents
        total_damage_poor_agents = sum(agent.flood_damage_estimated for agent in self.schedule.agents if agent.income_label == 'Poor')
        total_damage_middle_class_agents = sum(agent.flood_damage_estimated for agent in self.schedule.agents if agent.income_label == 'Middle-Class')
        total_damage_rich_agents = sum(agent.flood_damage_estimated for agent in self.schedule.agents if agent.income_label == 'Rich')

        #Calculate the average damage per agent of income class by dividing it with the number of agents of that income class in the model
        average_damage_per_poor_agent = total_damage_poor_agents/len(poor_agents)
        average_damage_per_middle_class_agent = total_damage_middle_class_agents/len(middle_class_agents)
        if len(rich_agents) > 0:
            average_damage_per_rich_agent = total_damage_rich_agents/len(rich_agents)
        else:
            return 'No Rich Agents in the model'

        #Append the values into the empty dictionary created at the beginning
        damage_per_agent_per_income_label['AverageDamagePerPoorHousehold'] = average_damage_per_poor_agent
        damage_per_agent_per_income_label['AverageDamagePerMiddleClassHousehold'] = average_damage_per_middle_class_agent
        damage_per_agent_per_income_label['AverageDamagePerRichHousehold'] = average_damage_per_rich_agent

        #The values are returned as a dictionary which will later be unpacked after the model has been run
        #This dictionary is unpacked into three seperate columns for each income label
        return damage_per_agent_per_income_label

    def calculate_average_income_to_damage_ratio(self):
        # Dictionary with the three labels and their respective average damage per agent in that label
        AverageIncomeToDamageRatio = {}

        # Create subsets of all the agents within the model based on income_label
        poor_agents = [agent for agent in self.schedule.agents if agent.income_label == 'Poor']
        middle_class_agents = [agent for agent in self.schedule.agents if agent.income_label == 'Middle-Class']
        rich_agents = [agent for agent in self.schedule.agents if agent.income_label == 'Rich']

        #Calculate the total damage per income label for all agents
        total_damage_poor_agents = sum(
            agent.flood_damage_actual for agent in self.schedule.agents if agent.income_label == 'Poor')
        total_damage_middle_class_agents = sum(
            agent.flood_damage_actual for agent in self.schedule.agents if agent.income_label == 'Middle-Class')
        total_damage_rich_agents = sum(
            agent.flood_damage_actual for agent in self.schedule.agents if agent.income_label == 'Rich')

        #Calculate the total income per income label for all agents of that income label
        total_income_poor_agents = sum(
            agent.income for agent in self.schedule.agents if agent.income_label == 'Poor')
        total_income_middle_class_agents = sum(
            agent.income for agent in self.schedule.agents if agent.income_label == 'Middle-Class')
        total_income_rich_agents = sum(
            agent.income for agent in self.schedule.agents if agent.income_label == 'Rich')

        #Calulcate the average damage per income label by dividing the total damage per income label by the number of agents with that income label
        average_damage_per_poor_agent = total_damage_poor_agents / len(poor_agents)
        average_damage_per_middle_class_agent = total_damage_middle_class_agents / len(middle_class_agents)
        if len(rich_agents) > 0:
            average_damage_per_rich_agent = total_damage_rich_agents / len(rich_agents)
        else:
            return 'No Rich Agents in the model'

        #Calulcate the average damage per income label by dividing the total damage per income label by the number of agents with that income label
        average_income_per_poor_agent = total_income_poor_agents / len(poor_agents)
        average_income_per_middle_class_agent = total_income_middle_class_agents / len(middle_class_agents)
        if len(rich_agents) > 0:
            average_income_per_rich_agent = total_income_rich_agents / len(rich_agents)
        else:
            return 'No Rich Agents in the model'

        #Calculate the average income to damage ratio by dividing average damage per agent / income class with the income
        #This shows the damage in relation to income, which is a way to calculate inequality
        #The higher
        AverageIncomeToDamageRatio[
            'AverageIncomeToDamagePoorHousehold'] = average_damage_per_poor_agent/average_income_per_poor_agent
        AverageIncomeToDamageRatio[
            'AverageIncomeToDamageMiddleClassHousehold'] = average_damage_per_middle_class_agent/average_income_per_middle_class_agent
        AverageIncomeToDamageRatio[
            'AverageIncomeToDamageRichHousehold'] = average_damage_per_rich_agent/average_income_per_rich_agent

        return AverageIncomeToDamageRatio

    def calculate_estimated_average_income_to_damage_ratio(self):
        # Dictionary with the three labels and their respective average damage per agent in that label
        AverageIncomeToDamageRatio = {}

        # Create subsets of all the agents within the model based on income_label
        poor_agents = [agent for agent in self.schedule.agents if agent.income_label == 'Poor']
        middle_class_agents = [agent for agent in self.schedule.agents if agent.income_label == 'Middle-Class']
        rich_agents = [agent for agent in self.schedule.agents if agent.income_label == 'Rich']

        #Calculate the total damage per income label for all agents
        total_damage_poor_agents = sum(
            agent.flood_damage_estimated for agent in self.schedule.agents if agent.income_label == 'Poor')
        total_damage_middle_class_agents = sum(
            agent.flood_damage_estimated for agent in self.schedule.agents if agent.income_label == 'Middle-Class')
        total_damage_rich_agents = sum(
            agent.flood_damage_estimated for agent in self.schedule.agents if agent.income_label == 'Rich')

        #Calculate the total income per income label for all agents of that income label
        total_income_poor_agents = sum(
            agent.income for agent in self.schedule.agents if agent.income_label == 'Poor')
        total_income_middle_class_agents = sum(
            agent.income for agent in self.schedule.agents if agent.income_label == 'Middle-Class')
        total_income_rich_agents = sum(
            agent.income for agent in self.schedule.agents if agent.income_label == 'Rich')

        #Calulcate the average damage per income label by dividing the total damage per income label by the number of agents with that income label
        average_damage_per_poor_agent = total_damage_poor_agents / len(poor_agents)
        average_damage_per_middle_class_agent = total_damage_middle_class_agents / len(middle_class_agents)
        if len(rich_agents) > 0:
            average_damage_per_rich_agent = total_damage_rich_agents / len(rich_agents)
        else:
            return 'No Rich Agents in the model'

        #Calulcate the average damage per income label by dividing the total damage per income label by the number of agents with that income label
        average_income_per_poor_agent = total_income_poor_agents / len(poor_agents)
        average_income_per_middle_class_agent = total_income_middle_class_agents / len(middle_class_agents)
        if len(rich_agents) > 0:
            average_income_per_rich_agent = total_income_rich_agents / len(rich_agents)
        else:
            return 'No Rich Agents in the model'

        #Calculate the average income to damage ratio by dividing average damage per agent / income class with the income
        #This shows the damage in relation to income, which is a way to calculate inequality
        #The higher
        AverageIncomeToDamageRatio[
            'AverageIncomeToDamagePoorHousehold'] = average_damage_per_poor_agent/average_income_per_poor_agent
        AverageIncomeToDamageRatio[
            'AverageIncomeToDamageMiddleClassHousehold'] = average_damage_per_middle_class_agent/average_income_per_middle_class_agent
        AverageIncomeToDamageRatio[
            'AverageIncomeToDamageRichHousehold'] = average_damage_per_rich_agent/average_income_per_rich_agent

        return AverageIncomeToDamageRatio

    def plot_model_domain_with_agents(self):
        fig, ax = plt.subplots()
        # Plot the model domain
        map_domain_gdf.plot(ax=ax, color='lightgrey')
        # Plot the floodplain
        floodplain_gdf.plot(ax=ax, color='lightblue', edgecolor='k', alpha=0.5)

        # Collect agent locations and statuses
        for agent in self.schedule.agents:
            color = 'blue' if agent.is_adapted else 'red'
            ax.scatter(agent.location.x, agent.location.y, color=color, s=10, label=color.capitalize() if not ax.collections else "")
            ax.annotate(str(agent.unique_id), (agent.location.x, agent.location.y), textcoords="offset points", xytext=(0,1), ha='center', fontsize=9)
        # Create legend with unique entries
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), title="Red: not adapted, Blue: adapted")

        # Customize plot with titles and labels
        plt.title(f'Model Domain with Agents at Step {self.schedule.steps}')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.show()

    def step(self):
        """
        introducing a shock: 
        at time step 5, there will be a global flooding.
        This will result in actual flood depth. Here, we assume it is a random number
        between 0.5 and 1.2 of the estimated flood depth. In your model, you can replace this
        with a more sound procedure (e.g., you can divide the flood map into zones and
        assume local flooding instead of global flooding). The actual flood depth can be 
        estimated differently
        """
        if self.schedule.steps == self.flood_step:
            for agent in self.schedule.agents:
                # Calculate the actual flood depth as a random number between 0.5 and 1.2 times the estimated flood depth
                agent.flood_depth_actual = random.uniform(0.5, 1.2) * agent.flood_depth_estimated
                # calculate the actual flood damage given the actual flood depth
                agent.flood_damage_actual = calculate_basic_flood_damage(agent.flood_depth_actual, agent.housesize)

                self.running = False

        self.total_adapted_households()
        self.total_actual_damage()
        self.total_expected_damage()
        # Collect data and advance the model by one step
        self.datacollector.collect(self)
        self.schedule.step()

    def model_run(self):
        for step in range(self.number_of_steps):
            self.step()

            # The model stops when the flood has taken place.
            # The set of rules for agents and their behavior flowing from this set is only relevant before a flood
            if step == self.flood_step:
                #self.plot_model_domain_with_agents()
                break


