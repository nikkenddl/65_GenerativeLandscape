# -*- coding: utf-8 -*-

import os
import json
import math

class Singleton(object):
    def __new__(cls, *args, **kargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super(Singleton, cls).__new__(cls)
        return cls._instance


class Config(Singleton):
    def __init__(self):
        self.__shade_tolerance = (6.0,4.0,2.0)
        self.__wind_tolerance = (4.3,5.6,float('inf'))
        self.__map_layer_name = "GH_MESH_GRIDMAP"
        self.__map_keys = (
            "x_cell_count",
            "y_cell_count",
            "grid_origin",
            "span",
            "is_cell_in_region_base64",
            "cell_z_value_base64",
            "sunshine_duration_hour_base64",
            "soil_thickness_base64",
            "wind_speed_base64",
            "FR_data_base64",
            "created_time"
        )
        self.__forest_region_layer = "GH_srf_forest-domain"
        self.__forest_region_archive_layer = "GH_mesh_forest_regions"
        self.__forest_region_keys = (
            "forest_region_ID",
            "forest_domain_name"
        )

        self.__path_forest_domain = os.path.abspath(os.path.join(
            __file__,
            os.pardir,
            os.pardir,
            os.pardir,
            os.pardir,
            "20_data",
            "forest_domain_data.xlsx"
        ))
        
    @property
    def shade_tolerance(self):
        return self.__shade_tolerance
    
    @property
    def wind_tolerance(self):
        return self.__wind_tolerance
    
    @property
    def map_layer_name(self):
        return self.__map_layer_name
    
    @property
    def map_keys(self):
        return self.__map_keys
    
    @property
    def forest_region_layer(self):
        return self.__forest_region_layer
    
    @property
    def forest_region_archive_layer(self):
        return self.__forest_region_archive_layer
    
    @property
    def forest_region_keys(self):
        return self.__forest_region_keys
    
    @property
    def path_forest_domain(self):
        return self.__path_forest_domain