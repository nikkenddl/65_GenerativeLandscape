# -*- coding: utf-8 -*-
# 
from .conversion import try_get_float
from .Cell import Cell
from .rhinopy import project_to_xyplane,compute_area
from .config import Config

class ForestDomain:
    def __init__(self,
                 name,
                 density,
                 low_tree_density,
                 overlap_tolerance_ratio,
                 count_top_layer_species,
                 eg_dd_ratio,
                 eg_dd_ratio_in_gap,
                 gap_size, 
                 dominant_species):
        self.name = str(name)
        assert density is not None

        # Convert density from trees per 100m^2 to trees per mm^2
        self.density = try_get_float(density) / (100 * 1000000)  # 1m² = 1000000mm²
        self.low_density = try_get_float(low_tree_density) / (100 * 1000000)  # 1m² = 1000000mm²

        self.overlap_tolerance_ratio = try_get_float(overlap_tolerance_ratio,False,0.0)
        self.vicinity_same_height_category_limit = int(count_top_layer_species)
        self.eg_ratio = try_get_float(eg_dd_ratio,False,0.5)
        self.eg_ratio_in_gap = try_get_float(eg_dd_ratio_in_gap,False,0.5)
        self.gap_size = try_get_float(gap_size,False,float('inf'))
        if self.gap_size: self.gap_size *= 1000000
        
        # Split dominant_species using '/' and store as a list
        self.dominant_species = set(dominant_species.split('/'))

        # set self information to Cell.FD_DICT (class attribute)
        Cell.set_FD(self)


        
    def copy(self):
        """Creates and returns a copy of the current ForestDomain instance."""
        new_instance = ForestDomain.__new__(ForestDomain)  # Create a new instance without calling __init__
        new_instance.name = self.name
        new_instance.density = self.density
        new_instance.overlap_tolerance_ratio = self.overlap_tolerance_ratio
        new_instance.vicinity_same_height_category_limit = self.vicinity_same_height_category_limit
        new_instance.eg_ratio = self.eg_ratio
        new_instance.eg_ratio_in_gap = self.eg_ratio_in_gap
        new_instance.gap_size = self.gap_size
        new_instance.dominant_species = set(self.dominant_species)  # Copy the list
        return new_instance

    def __str__(self):
        return ("ForestDomain<{}>").format(self.name)
    

class ForestRegion:
    __config = Config()
    def __init__(self, ID, region_mesh, forest_domain):
        self.ID = int(ID)
        self.region_mesh = region_mesh
        self.region_mesh_projected = project_to_xyplane(self.region_mesh)
        self.forest_domain = forest_domain
        self.__area = compute_area(self.region_mesh_projected)
        self.__limit_tree_count = self.__area * self.forest_domain.density
        self.__limit_tree_count_lower = self.__area * self.forest_domain.low_density
        
        # add when Cell is istanced.
        self.cells = []
        self.__has_been_finished_placement = False
        self.__has_been_finished_placement_lower = False

        # set self information to Cell.FR_DICT (class attribute)
        Cell.set_FR(self)

        eval_dominant = 0.0
        eval_egdd = 0.0

    def initialize(self):
        self.__has_been_finished_placement = False

    @property
    def area(self):
        return self.__area
    
    @property
    def limit_tree_count(self):
        return self.__limit_tree_count
    
    @property
    def FD_dominant_species(self):
        return self.forest_domain.dominant_species

    @property
    def FD_eg_ratio(self):
        return self.forest_domain.eg_ratio
    
    @property
    def placed_trees(self):
        return [c.placed_tree for c in self.cells if c.placed_tree]
    
    @property
    def has_finished_placement(self):
        return self.__has_been_finished_placement
    
    @property
    def has_finished_placement_lower(self):
        return self.__has_been_finished_placement_lower
    
    def update_has_been_finished(self):
        # density should be calculated with only trees whose height category is over tolerance.
        tol = self.__config.high_tree_shortest_height_class
        self.__has_been_finished_placement = sum(t.height_category>=tol for t in self.placed_trees)>self.__limit_tree_count

    def update_has_been_finished_lower(self):
        # density should be calculated with only trees whose height category is over tolerance.
        tol = self.__config.high_tree_shortest_height_class
        self.__has_been_finished_placement_lower = sum(t.height_category<tol for t in self.placed_trees)>self.__limit_tree_count_lower

    def evaluate_dominant(self):
        """Evaluates the ratio of dominant species in placed trees and compares it to the target ratio.

        Returns
        -------
        tuple
            - eval_value (float): The ratio of dominant species in the placed trees.
            - goal_over_eval (float): The ratio of the target dominant species ratio to the current ratio.
        """
        trees = self.placed_trees
        if not trees:
            return 1.0,0.5
        
        eval_count = sum(t.species in self.FD_dominant_species for t in trees)
        eval_value = float(eval_count) / float(len(trees))
        goal_value = float(self.__config.dominant_species_ratio)

        if eval_value==0.0:
            goal_over_eval = 10
        else:
            goal_over_eval = goal_value/eval_value

        return eval_value,goal_over_eval
    
    def evaluate_egdd(self):
        """Evaluates the ratio of evergreen trees in placed trees and compares it to the target ratio.

        Returns
        -------
        tuple
            - eval_value (float): The ratio of evergreen trees in the placed trees.
            - goal_over_eval (float): The ratio of the target evergreen tree ratio to the current ratio.
        """
        trees = self.placed_trees
        if not trees:
            return 1.0,0.5
        
        eval_count = sum(t.is_evergreen for t in trees)
        eval_value = float(eval_count) / float(len(trees))
        goal_value = float(self.FD_eg_ratio)

        if eval_value==0.0:
            goal_over_eval = 10
        else:
            goal_over_eval = goal_value/eval_value

        return eval_value,goal_over_eval

    def __str__(self):
        return "ForestRegion(ID:{} / FD:{})".format(self.ID,self.forest_domain.name)

    
    def __eq__(self, other):
        if not isinstance(other, ForestRegion):
            return False
        return self.ID == other.ID

    def __hash__(self):
        return hash(self.ID+1524)