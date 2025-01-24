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
        self.__map_layer_name = "FOREST-CREATOR-DATA_map"
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
        self.__forest_region_archive_layer = "FOREST-CREATOR-DATA_forest-region"
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

        self.__preplaced_tag = "preplaced-tree"

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
        self.__tree_asset_table_col_is_evergreen = "常緑"
        self.__tree_asset_table_col_is_conifers = "針葉"
        self.__tree_asset_table_col_undercut_height_ratio = "下枝高さ比率"

        self.__tree_height_category = [8000,5000,3000,2000]
        self.__tree_height_category.sort(reverse=True)

        self.__required_sunshine_duration_hour_by_shade_tolerance = (6.0,4.0,2.0)
        self.__limit_wind_speed_by_wind_tolerance = (4.3,5.6,float('inf'))
        self.__tree_height_lower_limit_to_consider_root_shape_for_soil_thickness = 8000.0 # mm
        self.__high_tree_shortest_height_class = 3000 # mm
        # use when tree height is equal or higher than __tree_height_lower_limit_to_consider_root_shape_for_soil_thickness
        self.__required_soil_thickness_by_root_type = {
            "A": 1500, # int
            "B": 1000, 
            "C": 1000 
        }
         # use when tree height is lower than __tree_height_lower_limit_to_consider_root_shape_for_soil_thickness
        self.__required_soil_thickness_by_height_category = {
            2000:0,
            3000:600,
            5000:600,
            8000:1000
        }

        tree_shape_section_2D_coordinates_typeA = ((1.0,0.0),(0.0,1.0),(-1.0,0.0)) # cone
        tree_shape_section_2D_coordinates_typeB = ((0.0,0.0),(0.134459,0.00454),(0.268285,0.01833),(0.400732,0.041902),(0.530792,0.076249),(0.656898,0.12301),(0.7763,0.184818),(0.883492,0.265777),(0.966226,0.371153),(1.0,0.5),(0.966226,0.628847),(0.883492,0.734223),(0.7763,0.815182),(0.656898,0.87699),(0.530792,0.923751),(0.400732,0.958098),(0.268285,0.98167),(0.134459,0.99546),(0.0,1.0),(-0.134459,0.99546),(-0.268285,0.98167),(-0.400732,0.958098),(-0.530792,0.923751),(-0.656898,0.87699),(-0.7763,0.815182),(-0.883492,0.734223),(-0.966226,0.628847),(-1.0,0.5),(-0.966226,0.371153),(-0.883492,0.265777),(-0.7763,0.184818),(-0.656898,0.12301),(-0.530792,0.076249),(-0.400732,0.041902),(-0.268285,0.01833),(-0.134459,0.00454)) # ellipse
        tree_shape_section_2D_coordinates_typeC = ((1.0,0.0),(1.0,1.0),(-1.0,1.0),(-1.0,0.0)) # cylinder
        tree_shape_section_2D_coordinates_typeD = ((0.0,0.0),(1.0,1.0),(-1.0,1.0)) # cone upside down

        self.__tree_shape_section_2D_dictionary = {
            "A" : tree_shape_section_2D_coordinates_typeA,
            "B" : tree_shape_section_2D_coordinates_typeB,
            "C" : tree_shape_section_2D_coordinates_typeC,
            "D" : tree_shape_section_2D_coordinates_typeD
        }

        __area_to_check_forest_layer_count = 100 # m2
        self.__radius_to_check_forest_layer_count = (__area_to_check_forest_layer_count/math.pi) ** (1/2) * 1000 #mm

        self.__radius_to_check_collision = 8000 * 2 # finding radius * 2

    @property
    def required_sunshine_duration_hour_by_shade_tolerance(self):
        return self.__required_sunshine_duration_hour_by_shade_tolerance
    
    @property
    def limit_wind_speed_by_wind_tolerance(self):
        return self.__limit_wind_speed_by_wind_tolerance
    
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
    
    @property
    def tree_asset_table_col_is_evergreen(self):
        return self.__tree_asset_table_col_is_evergreen
    @property
    def tree_asset_table_col_is_conifers(self):
        return self.__tree_asset_table_col_is_conifers
    
    @property
    def tree_asset_table_col_undercut_height_ratio(self):
        return self.__tree_asset_table_col_undercut_height_ratio
    
    @property
    def tree_height_category(self):
        """Desc sorted tree height category.

        Returns
        -------
        height_category: (n,) int
            desc sorted.
        """
        return self.__tree_height_category
    
    @property
    def high_tree_shortest_height_class(self):
        return self.__high_tree_shortest_height_class

    @property
    def tree_height_lower_limit_to_consider_root_shape_for_soil_thickness(self):
        return self.__tree_height_lower_limit_to_consider_root_shape_for_soil_thickness
    
    @property
    def required_soil_thickness_by_root_type(self):
        """use when tree height is equal or higher than Config.tree_height_lower_limit_to_consider_root_shape_for_soil_thickness
        """
        return self.__required_soil_thickness_by_root_type
    
    @property
    def tree_shape_section_2D_dictionary(self):
        """use when tree height is lower than Config.tree_height_lower_limit_to_consider_root_shape_for_soil_thickness.
        """
        return self.__tree_shape_section_2D_dictionary
    
    @property
    def required_soil_thickness_by_height_category(self):
        """use when tree height is lower than Config.tree_height_lower_limit_to_consider_root_shape_for_soil_thickness.
        """
        return self.__required_soil_thickness_by_height_category
    
    @property
    def radius_to_check_forest_layer_count(self):
        return self.__radius_to_check_forest_layer_count
    
    @property
    def radius_to_check_collision(self):
        return self.__radius_to_check_collision
    
    @property
    def preplaced_tag(self):
        return self.__preplaced_tag