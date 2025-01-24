# -*- coding: utf-8 -*-
from .conversion import *
from .config import Config
from .rhinopy import PolylineBoolenCalculation
from .Cell import Cell
from copy import copy
from math import floor
from collections import Iterable


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
                 is_conifers=None,
                 undercut_height_ratio=None):

        self.species = try_get_text(species)
        self.symbol = try_get_text(symbol)
        self.height = try_get_float(height) * 1000 # convert from m to mm
        self.height_category = self.get_height_category(self.height)
        # ignore error because circumuference include "株立"
        self.trunk_circumference = try_get_float(trunk_circumference,False) * 1000 # convert from m to mm
        self.diameter = try_get_float(diameter) * 1000 # convert from m to mm
        self.maximum_height = try_get_float(maximum_height) * 1000 # convert from m to mm
        self.undercut_height_ratio = try_get_float(undercut_height_ratio)

        self.__shade_tolerance_index = try_get_int(shade_tolerance)
        self.__wind_tolerance_index = try_get_int(wind_tolerance)
        self.shape_type = try_get_text(shape_type)
        self.root_type = try_get_text(root_type)
        self.growing_speed = try_get_text(growing_speed)
        self.is_evergreen = try_convert_strbool_to_bool(is_evergreen)
        self.is_conifers = try_convert_strbool_to_bool(is_conifers)

        self.placed_cell = None
        self.__placed_point = None
        self.__overlapped_trees = []
        self.is_damy = False

        self.required_shade_tolerance = None
        self.limit_wind_tolerance = None
        self.required_soil_thickness = None
        self.tree_shape_section = None
        self.root = None
        self.section_area = None

        self.custom_tags = set()

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
        if self.shape_type is not None:
            self.tree_shape_section = self.get_tree_shape_section(self.radius,self.height,self.undercut_height_ratio,self.shape_type)
            self.section_area = self.compute_area_of_coordinates(self.tree_shape_section)

    def init_list_contents(self):
        self.__overlapped_trees = []
        self.custom_tags = set()
    
    @staticmethod
    def compute_area_of_coordinates(coordinates):
        def cross(v1, v2):
            return v1[0] * v2[1] - v1[1] * v2[0]

        area = 0
        for i in range(len(coordinates) - 1):
            area += cross(coordinates[i], coordinates[i + 1])
        area += cross(coordinates[-1],coordinates[0])

        return abs(area / 2)

    @classmethod
    def get_tree_shape_section(cls,canopy_radius,tree_height,undercut_hegiht_ratio,tree_shape_type):
        base_coordinates = cls.__config.tree_shape_section_2D_dictionary[tree_shape_type]

        canopy_height = tree_height*(1.0-undercut_hegiht_ratio)
        undercut_height = tree_height*undercut_hegiht_ratio

        # scale
        shape_section_coordinates = [(p[0]*canopy_radius,p[1]*canopy_height+undercut_height) for p in base_coordinates]
        return shape_section_coordinates

    @classmethod
    def get_height_category(cls,height):
        return next(h for h in cls.__config.tree_height_category if int(floor(height))>=h)
    
    @property
    def is_placed(self):
        return not self.is_damy and self.placed_cell is not None

    @property
    def radius(self):
        return self.diameter/2
    
    @property
    def overlapped_trees(self):
        return copy(self.__overlapped_trees)
    
    def copy(self):
        new = copy(self)
        new.init_list_contents()
        return new
    
    def register_custom_tag(self,string):
        if isinstance(string,str):
            self.custom_tags.add(string)
        
    def has_tag(self,tag_string):
        return tag_string in self.custom_tags
    
    def register_overlapped_tree(self,tree):
        return self.__overlapped_trees.append(tree)
    
    def register_overlapped_trees(self,trees):
        return self.__overlapped_trees.extend(trees)
    
    def __str__(self):
        if self.__placed_point and self.placed_cell:
            return "Tree<{}/{}/cell[{}]>".format(self.symbol,self.species,self.placed_cell.ID)
        else:
            return "Tree<{}/{}>".format(self.symbol,self.species)
        
    @property
    def point(self):
        if not self.__placed_point: return None
        else: return self.__placed_point

    def set_placed_point(self,point):
        self.__placed_point = point
    
    def get_damy_pointed_tree(self,point):
        new = self.copy()
        new.set_placed_point(point)
        new.is_damy = True
        return new
    
    def place(self,cell,is_damy=False):
        if not cell: raise Exception("cell is not existing")
        new = self.copy()
        new.placed_cell = cell
        new.set_placed_point(cell.point)

        if not is_damy:
            # add this tree to cell.
            cell.placed_tree = new
            # update forest_region status.
            cell.forest_region.update_has_been_finished()
        else:
            new.is_damy = True
        return new
    

    def place_with_point(self,point,cells,is_damy=False):
        id_of_cell = Cell.get_cell_ID_of_point(point)
        try:
            cell = next(cell for cell in cells if cell.ID==id_of_cell)
        except StopIteration as e:
            print("not found cell whose id=={}".format(id_of_cell))
            return None
        except Exception as e:
            raise Exception("strange error ",e )

        new = self.copy()
        new.placed_cell = cell
        new.set_placed_point(point)

        if not is_damy:
            # add this tree to cell.
            cell.placed_tree = new
            # update forest_region status.
            cell.forest_region.update_has_been_finished()
        else:
            new.is_damy = True
        return new
    

        


    
    def matches_cell_environment(self,testing_cell):
        """Check if this tree can be planted in the testing cell.

        Parameters
        ----------
        testing_cell : Cell

        Returns
        -------
        is_placable: bool
        status: str
        """
        # check sunduraiton hour
        if testing_cell.sunshine_duration < self.required_shade_tolerance:
            return False,"sunshine duration is too short"

        # check wind speed
        if testing_cell.wind_speed > self.limit_wind_tolerance:
            return False,"wind speed is too fast"
        
        # check soil thickness
        if testing_cell.soil_thickness < self.required_soil_thickness:
            return False,"soil thickness is too thin"
        
        # default
        return True,"ok"
    
    def get_overlapping_ratio(self,neighbor_trees,self_tree_origin=None):
        """_summary_

        Parameters
        ----------
        neighbor_trees : (n,) Tree
        self_tree_origin : Rhino.Geometry.Point3d, optional
            Override self.point to get overlaping trees before placement, by default None

        Returns
        -------
        overlap_ratio: float
        overlap_neighbors: (n,) Tree

        """
        def translate_coordinates(coordinates,vec):
            return [(c[0]+vec[0],c[1]+vec[1]) for c in coordinates]
        
        if self.section_area is None: # other trees has been set = must have section_area attribute.
            raise Exception("Tree area is not set")
        if self_tree_origin is None and self.point is None: # other tree has been set = must have point attribute.
            raise Exception("To compute canopy overlapping area, self and other trees must already have been placed.\nYou can specify damy origin for self via the parameter 'self_tree_origin'.\n self.placed_cell: {}\nother_tree.placed_cell: {}".format(self.placed_cell,neighbor.placed_cell))

        self_point = self_tree_origin or self.point

        # find overlapped trees and its intersectioned area
        overlap_neighbors = []
        intersected_area = 0.0
        for neighbor in neighbor_trees:
            xy_dist = (
                    (neighbor.point.X - self_point.X)**2
                   +(neighbor.point.Y - self_point.Y)**2
                )**(1.0/2.0)
            z_dist = neighbor.point.Z - self_point.Z
            vec = (xy_dist,z_dist)

            other_tree_shape_section_translated = translate_coordinates(neighbor.tree_shape_section,vec)
            overlap_region_as_pathsD = PolylineBoolenCalculation.intersect_polyline(pl1=self.tree_shape_section,
                                                                                    pl2=other_tree_shape_section_translated,
                                                                                    use_rhino=False,
                                                                                    return_clipper_path=True)
            if overlap_region_as_pathsD.Count>0:
                for pathD in overlap_region_as_pathsD:
                    intersected_area += PolylineBoolenCalculation.get_area_of_clipper_path(pathD)
                overlap_neighbors.append(neighbor)
        
        overlap_ratio = intersected_area / self.section_area
        print(overlap_ratio)
        return overlap_ratio,overlap_neighbors

    def recheck_overlap(self,extra_tree,extra_tree_origin):
        """_summary_

        Parameters
        ----------
        extra_tree : Tree
        extra_tree_origin : Rhino.Geometry.Point3d

        Returns
        -------
        is_acceptable: bool
            This tree can be placed if extra_tree is added.
        """
        if not self.is_placed: raise Exception("Placed trees can be rechecked.")

        added_tree = extra_tree.get_damy_pointed_tree(extra_tree_origin)
        overlapped_trees = self.overlapped_trees
        overlapped_trees.append(added_tree)

        ov_ratio,_ = self.get_overlapping_ratio(overlapped_trees)
        
        return ov_ratio<=self.placed_cell.FD_overlap_tolerance_ratio






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
            "is_conifers":cls.__config.tree_asset_table_col_is_conifers,
            "undercut_height_ratio":cls.__config.tree_asset_table_col_undercut_height_ratio
        } #TreeType init args: this function args

        args_col_names = {key:value for key,value in args_col_names.items() if value is not None}

        headers = database_matrix.pop(0)
        args_indices = {key: headers.index(value) for key,value in args_col_names.items() if value is not None} # Ignore args that are None
        tree_assets = [Tree(**{key: row[index] for key,index in args_indices.items()}) for row in database_matrix]
        return tree_assets


        
class PlacementPostponedTree:
    __config = Config()
    def __init__(self,tree,point,cell,custom_tags=None):
        self.tree = tree
        self.cell = cell
        self.point = point
        if custom_tags:
            if isinstance(custom_tags,str):
                self.custom_tags = [custom_tags]
            elif isinstance(custom_tags,Iterable):
                self.custom_tags = [str(tag) for tag in custom_tags]
            else:
                self.custom_tags = [str(custom_tags)]
        else:
            self.custom_tags = []
        self.custom_tags.append(self.__config.preplaced_tag)
        
    def place(self):
        placed = self.tree.place(self.cell)
        if placed: # if point is out of map, place_with_point() returns None.
            placed.set_placed_point(self.point) # override placed point by the accurate point.
            for tag in self.custom_tags:
                placed.register_custom_tag(tag)
            return placed
        else:
            return None
        
    def place_damy(self):
        new = self.tree.get_damy_pointed_tree(self.point)
        for tag in self.custom_tags:
            new.register_custom_tag(tag)
        return new