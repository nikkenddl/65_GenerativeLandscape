# -*- coding: utf-8 -*-
from .conversion import *
from copy import copy

class TreeType:
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
        self.shade_tolerance = try_get_int(shade_tolerance)
        self.wind_tolerance = try_get_int(wind_tolerance)
        self.shape_type = try_get_text(shape_type)
        self.root_type = try_get_text(root_type)
        self.growing_speed = try_get_text(growing_speed)
        self.placed_coordinates = None

    @property
    def radius(self):
        return self.diameter/2
    
    def __str__(self):
        if self.placed_coordinates:
            return "TreeType<{}/{}/{}>".format(self.symbol,self.species,self.placed_coordinates)
        else:
            return "TreeType<{}/{}>".format(self.symbol,self.species)
    
    def place(self,point):
        new = copy(self)
        new.placed_coordinates = (float(point.X),float(point.Y),float(point.Z))
        return new

    

    
def generate_treetypes_from_database(database_matrix,
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
    tree_assets = [TreeType(**{key: row[index] for key,index in args_indices.items()}) for row in database_matrix]
    return tree_assets


        
