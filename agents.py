"""
Part of Chitwan Valley agent-based model.

Class for person, household, neighborhood, and region agents.

Alex Zvoleff, azvoleff@mail.sdsu.edu
"""

import numpy as np

from chitwanABM import rcParams, IDGenerator, boolean_choice
from chitwanABM.landuse import LandUse

class Agent(object):
    "Superclass for agent objects."
    def __init__(self, IDGen, ID=None, initial_agent=False):
        # self._ID is unique ID number used to track each person agent.
        if ID == None:
            self._ID = IDGen.next()
        else:
            IDGen.use_ID(ID) # Update the generator so ID will not be reused
            self._ID = ID

        # Save a reference to the IDGenerator so it can be used later
        self._IDGen = IDGen

        # self._initial_agent is set to "True" for agents that were used to 
        # initialize the model.
        self._initial_agent = initial_agent

    def get_ID(self):
        return self._ID

    def set_ID(self, ID):
        self._IDGen.use_ID(ID) # Update the generator so ID will not be reused
        self._ID = ID

class Agent_set(Agent):
    """Superclass for agents that contain a "set" of agents from a lower 
    hierarchical  level."""
    def __init__(self, IDGen, ID, initial_agent):
        Agent.__init__(self, IDGen, ID, initial_agent)

        # _members stores agent set members in a dictionary keyed by ID
        self._members = {}

    def get_agents(self):
        return self._members.values()

    def get_agent(self, ID):
        return self._members[ID]

    def add_agent(self, agent):
        "Adds a new agent to the set."
        if self._members.has_key(agent.get_ID()):
            raise KeyError("agent %s is already a member of agent set %s"%(agent.get_ID(), self._ID))
        self._members[agent.get_ID()] = agent

    def remove_agent(self, person):
        "Removes an agent from agent set"
        try:
            self._members.pop(person.get_ID())
        except KeyError:
            raise KeyError("agent %s is not a member of agent set %s"%(person.get_ID(), self._ID))

    def num_members(self):
        return len(self._members)

# PIDGen generates unique ID numbers that are never reused (once used an ID 
# number cannot be reassigned to another agent). All instances of the Person 
# class will have a unique ID number generated by the PIDGen instance.
PIDGen = IDGenerator()
class Person(Agent):
    "Represents a single person agent"
    def __init__(self, birthdate, PID=None, mother_ID=None, father_ID=None,
            age=0, sex=None, initial_agent=False):
        Agent.__init__(self, PIDGen, PID, initial_agent)

        # birthdate is the timestep of the birth of the agent. It is used to 
        # calculate the age of the agent. Agents have a birthdate of 0 if they 
        # were BORN in the first timestep of the model.  If they were used to 
        # initialize the model their birthdates will be negative.
        self._birthdate = birthdate
        # deathdate is used for tracking agent deaths in the results, mainly 
        # for debugging.
        self._deathdate = None

        # self._initial_agent is set to "True" for agents that were used to 
        # initialize the model.
        self._initial_agent = initial_agent

        # self._age is used as a convenience to avoid the need to calculate 
        # the agent's age from self._birthdate each time it is needed. It is         
        # important to remember though that all agent's ages must be 
        # incremented with each model timestep. The age starts at 0 (it is 
        # zero for the entire first timestep of the model).
        self._age = age

        # Also need to store information on the agent's parents. For agents 
        # used to initialize the model both parent fields are set to "None"
        if father_ID == None:
            self._father_ID = None
        else:
            self._father_ID = father.get_ID()

        if mother_ID == None:
            self._mother_ID = None
        else:
            self._mother_ID = mother.get_ID()

        if sex==None:
            # Person agents are randomly assigned a sex
            if boolean_choice(.5):
                self._sex = 'female'
            else:
                self._sex = 'male'
        else:
            self._sex = sex

        self._spouseID = None

        self._children = []

    def get_sex(self):
        return self._sex

    def get_spouse_ID(self):
        return self._spouseID

    def marry(self, other):
        "Marries this agent to another Person instance."
        self._spouseID = other.get_ID()
        other._spouseID = self.get_ID()

    def give_birth(self, time, dad):
        "Agent gives birth. New agent inherits characterists of parents."
        assert self.get_sex() == 'female', "Men can't give birth"
        assert self.get_ID() != dad.get_ID(), "No immaculate conception"
        assert self.get_spouse_ID() == dad.get_ID(), "All births must be in marriages"
        baby = Person(birthdate=time, mother=self, father=dad)
        for parent in [self, dad]:
            parent._children.append(baby)
        return baby

    def is_married(self):
        "Returns a boolean indicating if person is married or not."
        if self._spouseID == None:
            return False
        else:
            return True

HIDGen = IDGenerator()
class Household(Agent_set):
    "Represents a single household agent"
    def __init__(self, ID=None, initial_agent=False):
        Agent_set.__init__(self, HIDGen, ID, initial_agent)
        self._any_non_wood_fuel = boolean_choice()
        self._own_house_plot = boolean_choice()
        self._own_land = boolean_choice()
        self._rented_out_land = boolean_choice()

    def any_non_wood_fuel(self):
        "Boolean for whether household uses any non-wood fuel"
        return self._any_non_wood_fuel

    def own_house_plot(self):
        "Boolean for whether household owns the plot of land on which it resides"
        return self._own_house_plot

    def own_any_land(self):
        "Boolean for whether household owns any land"
        return self._own_land

    def rented_out_land(self):
        "Boolean for whether household rented out any of its land"
        return self._rented_out_land

NIDGen = IDGenerator()
class Neighborhood(Agent_set):
    "Represents a single neighborhood agent"
    def __init__(self, ID=None, initial_agent=False):
        Agent_set.__init__(self, NIDGen, ID, initial_agent)
        self._avg_years_nonfamily_services = None
        self._elec_available = None

    def avg_years_nonfamily_services(self):
        "Average number of years non-family services have been available."
        return self._avg_years_nonfamily_services

    def elec_available(self):
        "Boolean for whether neighborhood has electricity."
        return self._elec_available

RIDGen = IDGenerator()
class Region(Agent_set):
    """Represents a set of neighborhoods sharing a spatial area (and therefore 
    land use data), and demographic characteristics."""
    def __init__(self, ID=None, initial_agent=False):
        Agent_set.__init__(self, RIDGen, ID, initial_agent)

        self._landuse = LandUse()
        
        # Now setup the demographic variables for this population, based on the 
        # values given in the model rc file
        self._hazard_birth = rcParams['hazard_birth']
        self._hazard_death = rcParams['hazard_death']
        self._hazard_marriage = rcParams['hazard_marriage']

    def __repr__(self):
        #TODO: Finish this
        return "__repr__ UNDEFINED"

    def __str__(self):
        return "Region(RID: %s. %s neighborhood(s), %s household(s), %s person(s))" %(self.get_ID(), len(self._members), self.get_num_households(), self.census())

    def births(self, time):
        """Runs through the population and agents give birth probabilistically 
        based on their sex, age and the hazard_birth for this population"""
        # TODO: This should take account of the last time the agent gave birth 
        # and adjust the hazard accordingly
        for neighborhood in self._members:
            for household in neighborhood.get_agents():
                for person in household.get_agents():
                    if (person.get_sex() == 'female') and (np.random.random()
                            < self._hazard_birth[person.get_age()]):
                                # Agent gives birth. First find the father 
                                # (assumed to be the spouse of the person 
                                # giving birth).
                                dad = household.get_person(
                                        person.get_spouseID())
                                # Now have the mother give birth, and add the 
                                # new person to the mother's household.
                                household.add_person(person.give_birth(time, 
                                    father=dad))
                        
    def deaths(self, time):
        """Runs through the population and kills agents probabilistically based 
        on their age and the hazard_death for this population"""
        for neighborhood in self._members:
            for household in neighborhood.get_agents():
                for person in household.get_agents():
                    if (person.get_sex() == 'female') and (np.random.random()
                            < self._hazard_death[person.get_age()]):
                                # Agent dies:
                                person.kill()
                                household.remove_agent(person.give_birth(time))
                        
    def marriages(self, time):
        """Runs through the population and marries agents probabilistically 
        based on their age and the hazard_marriage for this population"""
        for neighborhood in self._members:
            for household in neighborhood.get_agents():
                for person in household.get_agents():
                    if (person.get_sex() == 'female') and (np.random.random()
                            < self._hazard_marriage[person.get_age()]):
                                # Agent gets married:
                                person.marry(person.get_ID())
                        
    def increment_age(self):
        """Adds one to the age of each agent. The units of age are dependent on 
        the units of the input rc parameters."""
        for neighborhood in self._members:
            for household in neighborhood.get_agents():
                for person in household.get_agents():
                    person._age += 1

    def update_landuse(self):
        """Using the attributes of the neighborhoods in the region, update the 
        landuse proportions using OLS"""

    def kill_agent(self):
        "Kills an agent, removing it from its household, and its marriage."

    def census(self):
        "Returns the number of persons in the population."
        total = 0
        for neighborhood in self.get_agents():
            for household in neighborhood.get_agents():
                total += household.num_members()
        return total

    def get_num_households(self):
        total = 0
        for neighborhood in self.get_agents():
            total += len(neighborhood.get_agents())
        return total
