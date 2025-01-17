# -*- coding: utf-8 -*-
from .conversion import *
from .config import Config
from copy import copy
from math import floor


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
                 growing_speed=None,
                 is_evergreen=None,
                 is_conifers=None):

        self.species = try_get_text(species)
        self.symbol = try_get_text(symbol)
        self.height = try_get_float(height) * 1000 # convert from m to mm
        self.height_category = self.get_height_category(self.height)
        # ignore error because circumuference include "株立"
        self.trunk_circumference = try_get_float(trunk_circumference,False) * 1000 # convert from m to mm
        self.diameter = try_get_float(diameter) * 1000 # convert from m to mm
        self.maximum_height = try_get_float(maximum_height) * 1000 # convert from m to mm

        self.__shade_tolerance_index = try_get_int(shade_tolerance)
        self.__wind_tolerance_index = try_get_int(wind_tolerance)
        self.shape_type = try_get_text(shape_type)
        self.root_type = try_get_text(root_type)
        self.growing_speed = try_get_text(growing_speed)
        self.is_evergreen = try_convert_strbool_to_bool(is_evergreen)
        self.is_conifers = try_convert_strbool_to_bool(is_conifers)

        self.placed_cell = None

        self.required_shade_tolerance = None
        self.limit_wind_tolerance = None
        self.required_soil_thickness = None
        self.shape = None
        self.root = None

        self.set_config_value()

    def set_config_value(self):
        def get_required_soil_thickness():
            # check soil thickness
            ## check tree height over tolerance should be check root shape.
            if self.height>=self.__config.tree_height_lower_limit_to_consider_root_shape_for_soil_thickness-0.001:
                ### get by root type
                tol = self.__config.required_soil_thickness_by_root_type[self.root_type]
            else:
                ### get by height category
                tol = self.__config.required_soil_thickness_by_height_category[self.height_category]
            return tol
        if self.__shade_tolerance_index is not None: # Always enter into because try_get_int raise exception when getting value is failed. Make if to avoid syntax warning.
            self.required_shade_tolerance = self.__config.required_sunshine_duration_hour_by_shade_tolerance[self.__shade_tolerance_index]
        if self.__wind_tolerance_index is not None: # Always enter into because try_get_int raise exception when getting value is failed. Make if to avoid syntax warning.
            self.limit_wind_tolerance = self.__config.limit_wind_speed_by_wind_tolerance[self.__wind_tolerance_index]
        if self.root_type is not None and self.height_category is not None:
            self.required_soil_thickness = get_required_soil_thickness()

    @classmethod
    def get_height_category(cls,height):
        return next(h for h in cls.__config.tree_height_category if int(floor(height))>=h)

    

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
    
    def matches_cell_environment(self,testing_cell):
        """Check if this tree can be planted in the testing cell.

        Parameters
        ----------
        testing_cell : Cell

        Returns
        -------
        is_placable: bool
        """
        # check sunduraiton hour
        if testing_cell.sunshine_duration < self.required_shade_tolerance:
            return False

        # check wind speed
        if testing_cell.wind_speed > self.limit_wind_tolerance:
            return False
        
        # check soil thickness
        if testing_cell.soil_thickness < self.required_soil_thickness:
            return False
        
        # default
        return True

    @classmethod
    def generate_trees_from_database(cls,database_matrix):
        args_col_names = {
            "species":cls.__config.tree_asset_table_col_species,
            "symbol":cls.__config.tree_asset_table_col_symbol,
            "height":cls.__config.tree_asset_table_col_height,
            "trunk_circumference":cls.__config.tree_asset_table_col_trunk_circumference,
            "diameter":cls.__config.tree_asset_table_col_diameter,
            "maximum_height":cls.__config.tree_asset_table_col_maximum_height,
            "shade_tolerance":cls.__config.tree_asset_table_col_shade_tolerance,
            "wind_tolerance":cls.__config.tree_asset_table_col_wind_tolerance,
            "shape_type":cls.__config.tree_asset_table_col_shape_type,
            "root_type":cls.__config.tree_asset_table_col_root_type,
            "growing_speed":cls.__config.tree_asset_table_col_growing_speed,
            "is_evergreen":cls.__config.tree_asset_table_col_is_evergreen,
            "is_conifers":cls.__config.tree_asset_table_col_is_conifers
        } #TreeType init args: this function args

        args_col_names = {key:value for key,value in args_col_names.items() if value is not None}

        headers = database_matrix.pop(0)
        args_indices = {key: headers.index(value) for key,value in args_col_names.items() if value is not None} # Ignore args that are None
        tree_assets = [Tree(**{key: row[index] for key,index in args_indices.items()}) for row in database_matrix]
        return tree_assets


        
