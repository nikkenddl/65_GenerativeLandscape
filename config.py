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

        path_project_root = os.path.abspath(os.path.join(
            __file__,
            os.pardir,
            os.pardir,
            os.pardir,
            os.pardir
        ))

        self.__path_forest_domain = os.path.abspath(os.path.join(
            path_project_root,
            "20_data",
            "forest_domain_data.xlsx"
        ))

        self.__path_tree_asset = os.path.abspath(os.path.join(
            path_project_root,
            "20_data",
            "tree_asset_table.xlsx"
        ))

        self.__tree_asset_table_col_species = "樹木名"
        self.__tree_asset_table_col_symbol = "記号"
        self.__tree_asset_table_col_height = "樹高"
        self.__tree_asset_table_col_trunk_circumference = "幹周"
        self.__tree_asset_table_col_diameter = "葉張"
        self.__tree_asset_table_col_maximum_height = "最大成長樹高"
        self.__tree_asset_table_col_shade_tolerance = "耐陰性"
        self.__tree_asset_table_col_wind_tolerance = "耐風性"
        self.__tree_asset_table_col_shape_type = "樹形タイプ"
        self.__tree_asset_table_col_root_type = "根の成長"
        self.__tree_asset_table_col_growing_speed = "成長速度"
        
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
    
    @property
    def path_tree_asset(self):
        return self.__path_tree_asset
    

    @property
    def tree_asset_table_col_species(self):
        return self.__tree_asset_table_col_species
    @property
    def tree_asset_table_col_symbol(self):
        return self.__tree_asset_table_col_symbol
    @property
    def tree_asset_table_col_height(self):
        return self.__tree_asset_table_col_height
    @property
    def tree_asset_table_col_trunk_circumference(self):
        return self.__tree_asset_table_col_trunk_circumference
    @property
    def tree_asset_table_col_diameter(self):
        return self.__tree_asset_table_col_diameter
    @property
    def tree_asset_table_col_maximum_height(self):
        return self.__tree_asset_table_col_maximum_height
    @property
    def tree_asset_table_col_shade_tolerance(self):
        return self.__tree_asset_table_col_shade_tolerance
    @property
    def tree_asset_table_col_wind_tolerance(self):
        return self.__tree_asset_table_col_wind_tolerance
    @property
    def tree_asset_table_col_shape_type(self):
        return self.__tree_asset_table_col_shape_type
    @property
    def tree_asset_table_col_root_type(self):
        return self.__tree_asset_table_col_root_type
    @property
    def tree_asset_table_col_growing_speed(self):
        return self.__tree_asset_table_col_growing_speed