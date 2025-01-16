# -*- coding: utf-8 -*-
from .conversion import *
from .config import Config
from copy import copy


class Void:
    def __init__(self,point,radius):
        self.point = point
        self.radius = try_get_float(radius)
    
    @property
    def diameter(self):
        return self.radius*2
    
    def __str__(self):
        return "Void<{}/{}>".format(self.radius,self.point)
    
    @staticmethod
    def create_with_circle(rhino_circle):
        return Void(rhino_circle.Center,rhino_circle.Radius)
    

class Tree:
    __config = Config()
    def __init__(self,
                 species=None,
                 symbol=None,
                 height=None,
                 trunk_circumference=None,
                 diameter=None,
                 maximum_height=None,
                 shade_tolerance=None,
                 wind_tolerance=None,
                 shape_type=None,
                 root_type=None,
                 growing_speed=None):

        self.species = try_get_text(species)
        self.symbol = try_get_text(symbol)
        self.height = try_get_float(height)
        self.trunk_circumference = try_get_float(trunk_circumference)
        self.diameter = try_get_float(diameter)
        self.maximum_height = try_get_float(maximum_height)

        self.__shade_tolerance_index = try_get_int(shade_tolerance)
        self.__wind_tolerance_index = try_get_int(wind_tolerance)
        self.shape_type = try_get_text(shape_type)
        self.root_type = try_get_text(root_type)
        self.growing_speed = try_get_text(growing_speed)

        self.placed_cell = None

        self.shade_tolerance = None
        self.wind_tolerance = None
        self.shape = None
        self.root = None
        self.set_config_value()

    def set_config_value(self):
        if self.__shade_tolerance_index is not None:
            self.shade_tolerance = self.__config.shade_tolerance[self.__shade_tolerance_index]
        if self.__wind_tolerance_index is not None:
            self.wind_tolerance = self.__config.wind_tolerance[self.__wind_tolerance_index]


    @property
    def radius(self):
        return self.diameter/2
    
    def __str__(self):
        if self.placed_cell:
            return "Tree<{}/{}/cell[{}]>".format(self.symbol,self.species,self.placed_cell.ID)
        else:
            return "Tree<{}/{}>".format(self.symbol,self.species)
        
    @property
    def point(self):
        if not self.placed_cell: return None
        else: return self.placed_cell.point
    
    def place(self,cell):
        if not cell: raise Exception("cell is not existing")
        new = copy(self)
        new.placed_cell = cell
        # add this tree to cell.
        cell.placed_tree = new
        # update forest_region status.
        cell.forest_region.update_has_been_finished()
        return new
    
    def matches_cell_environment(self,cell):
        # check sunduraiton hour
        if cell.sunshine_duration < self.shade_tolerance:
            return False

        # # check wind speed
        if cell.wind_speed > self.wind_tolerance:
            return False
        
        # default
        return True

    @staticmethod
    def generate_trees_from_database(database_matrix,
                                     col_species=None,
                                     col_symbol=None,
                                     col_height=None,
                                     col_trunk_circumference=None,
                                     col_diameter=None,
                                     col_maximum_height=None,
                                     col_shade_tolerance=None,
                                     col_wind_tolerance=None,
                                     col_shape_type=None,
                                     col_root_type=None,
                                     col_growing_speed=None,
                                     ):
        args_col_names = {
            "species":col_species,
            "symbol":col_symbol,
            "height":col_height,
            "trunk_circumference":col_trunk_circumference,
            "diameter":col_diameter,
            "maximum_height":col_maximum_height,
            "shade_tolerance":col_shade_tolerance,
            "wind_tolerance":col_wind_tolerance,
            "shape_type":col_shape_type,
            "root_type":col_root_type,
            "growing_speed":col_growing_speed,
        } #TreeType init args: this function args

        args_col_names = {key:value for key,value in args_col_names.items() if value is not None}

        headers = database_matrix.pop(0)
        args_indices = {key: headers.index(value) for key,value in args_col_names.items() if value is not None} # Ignore args that are None
        tree_assets = [Tree(**{key: row[index] for key,index in args_indices.items()}) for row in database_matrix]
        return tree_assets


        
