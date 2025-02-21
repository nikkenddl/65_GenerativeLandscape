# -*- coding: utf-8 -*-
from .conversion import *
from .config import Config
from .rhinopy import PolylineBoolenCalculation
from .Cell import Cell
from copy import copy,deepcopy
from math import floor,log
from collections import Iterable # type: ignore


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
                 root_diameter=None,
                 safety_distance=None,
                 maximum_height=None,
                 shade_tolerance=None,
                 wind_tolerance=None,
                 shape_type=None,
                 root_type=None,
                 growing_speed=None,
                 is_evergreen=None,
                 is_conifers=None,
                 undercut_height_ratio=None,
                 growing_parameter_k=None,
                 growing_parameter_B=None):
        self.placed_cell = None
        self.__placed_point = None
        self.__age_estimation_cache = {}
        self.__height_estimation_cache = {}
        self.__tree_shape_cache = {} # hegiht: (polyline coordinates, section_area)

        self.species = try_get_text(species)
        self.symbol = try_get_text(symbol)
        self.__height = try_get_float(height) * 1000.0 # convert from m to mm
        self.height_category = self.get_height_category(self.__height)
        # ignore error because circumuference include "株立"
        self.trunk_circumference = try_get_float(trunk_circumference,False) * 1000.0 # convert from m to mm
        self.maximum_height = try_get_float(maximum_height) * 1000.0 # convert from m to mm
        self.undercut_height_ratio = try_get_float(undercut_height_ratio)

        # diameter and radius will be got from tree height and d/h ratio
        diameter = try_get_float(diameter) * 1000.0 # convert from m to mm
        self.DH_ratio = diameter/self.__height
        self.__initial_height = self.__height
        self.__initial_radius = self.radius

        self.__root_radius = try_get_float(root_diameter) * 500.0
        self.safety_distance = try_get_float(safety_distance) * 1000.0

        self.__shade_tolerance_index = try_get_int(shade_tolerance)
        self.__wind_tolerance_index = try_get_int(wind_tolerance)
        self.shape_type = try_get_text(shape_type)
        self.root_type = try_get_text(root_type)
        self.growing_speed = try_get_text(growing_speed)
        self.is_evergreen = try_convert_strbool_to_bool(is_evergreen)
        self.is_conifers = try_convert_strbool_to_bool(is_conifers)

        self.growing_parameter_k = try_get_float(growing_parameter_k)
        self.growing_parameter_B = try_get_float(growing_parameter_B)
        self.__initial_age = 0.0
        self.__age = 0.0
        self.__init_age()

        self.__overlapped_trees = []
        self.is_damy = False

        self.required_shade_tolerance = None
        self.limit_wind_tolerance = None
        self.required_soil_thickness = None
        self.root = None

        self.custom_tags = set()

        self.set_config_value()


    @property
    def height(self):
        return self.apply_height_limit_by_soil_thickness(try_get_float(self.__height))
    
    @property
    def age(self):
        return self.__age
    
    @property
    def initial_age(self):
        return self.__initial_age
    
    @property
    def initial_height(self):
        return self.__initial_height
    
    @property
    def initial_radius(self):
        return self.__initial_radius

    @property
    def tree_shape_section(self):
        return self.get_tree_shape_info()[0]

    def set_config_value(self):
        assert self.age==self.initial_age
        def get_required_soil_thickness():
            # check soil thickness
            ## check tree height over tolerance should be check root shape.
            if self.__height>=self.__config.tree_height_lower_limit_to_consider_root_shape_for_soil_thickness-0.001:
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

    def init_list_contents(self):
        self.__overlapped_trees = []
        self.custom_tags = set()

    
    def apply_height_limit_by_soil_thickness(self,height): 
        if not self.placed_cell: 
            rst = height
        else: 
            rst = max(min(height,self.placed_cell.tree_height_limit),self.__initial_height)
        return rst

        
    def __update_attributes_of_age(self,age):
        self.__age = age
        self.__height = self.estimate_height(self.__age)
        #self.height_category = self.get_height_category(self.__height) # do not change height category by age.

    def get_attributes_of_age(self,age):
        height = self.estimate_height(age)
        radius = self.estimate_radius_from_height(height)
        height_category = self.get_height_category(height)
        tree_shape_section = self.get_tree_shape_info(height)[0]
        return height,radius,height_category,tree_shape_section


    def timetravel(self,years):
        if years!=0 and years!=0.0:
            age = self.age + years
            self.timetravel_at(age)

    def timetravel_at(self,age):
        if age<=0:
            age = self.__initial_age
        self.__update_attributes_of_age(age)
    
    def __init_age(self):
        assert self.__height is not None
        self.__initial_age = self.estimate_age(self.__height) # type: ignore
        self.__age = self.__initial_age


    def get_tree_shape_info(self,height=None):
        """Get tree shape and area from cache.
        If information is not computed yet, compute information and cahche them.

        Parameters
        ----------
        height : float, optional
            use self.height if None is inptuted, default by None

        Returns
        -------
        tuple
        - tree_shape_section: (n,2) float
        - tree_shape_area: float
        """
        height = height or self.height
        if height in self.__tree_shape_cache:
            return self.__tree_shape_cache[height]
        else:
            radius = self.estimate_radius_from_height(height)
            tree_shape_section = self.compute_tree_shape_section(radius,height,self.undercut_height_ratio,self.shape_type)
            tree_shape_area = self.compute_area_of_coordinates(tree_shape_section)
            self.__tree_shape_cache[height] = (tree_shape_section,tree_shape_area)
            return (tree_shape_section,tree_shape_area)


    def estimate_age(self,height):
        if height in self.__age_estimation_cache:
            return self.__age_estimation_cache[height]
        else:
            age = self.__reverse_gompertz(height) if self.is_conifers else self.__reverse_mitcherlich(height)
            self.__age_estimation_cache[height] = age
            return age
    
    def estimate_height(self,age):
        if age in self.__height_estimation_cache:
            return self.apply_height_limit_by_soil_thickness(self.__height_estimation_cache[age])
        else:
            height = self.__gompertz(age) if self.is_conifers else self.__mitscherlich(age)
            self.__height_estimation_cache[age] = height
            return self.apply_height_limit_by_soil_thickness(height)
        
    def estimate_radius_from_age(self,age):
        height = self.estimate_height(age)
        return self.estimate_radius_from_height(height)
    
    def estimate_radius_from_height(self,height):
        return 0.5 * self.DH_ratio * height
    
    def estimate_future_height(self,year):
        if year==0 or year==0.0: return self.height
        age = self.age + year
        return self.estimate_height(age)
    
    def estimate_future_radius(self,year):
        if year==0 or year==0.0: return self.radius
        age = self.age + year
        return self.estimate_radius_from_age(age)

    def __reverse_mitcherlich(self,height):
        if (height>=self.maximum_height-0.001):
            return 200
        else:
            return log(1-height/self.maximum_height,self.growing_parameter_k)
    
    def __reverse_gompertz(self,height):
        if (height>=self.maximum_height-0.001):
            return 200
        else:
            return log(
                        log(
                            height/self.maximum_height,self.growing_parameter_B
                        ), self.growing_parameter_k)

    def __mitscherlich(self,age):
        return self.maximum_height * (1-self.growing_parameter_k**age)
    
    def __gompertz(self,age):
        return self.maximum_height * (self.growing_parameter_B**(self.growing_parameter_k**age))

    
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
    def compute_tree_shape_section(cls,
                               canopy_radius,
                               tree_height,
                               undercut_hegiht_ratio,
                               tree_shape_type):
        """_summary_

        Parameters
        ----------
        canopy_radius : _type_
        tree_height : _type_
        undercut_hegiht_ratio : _type_
        tree_shape_type : _type_

        Returns
        -------
        shape coordinates: (n,2)
            [(x1,y1), (x2,y2)...]
        """
        base_coordinates = cls.__config.tree_shape_section_2D_dictionary[tree_shape_type]

        canopy_height = tree_height*(1.0-undercut_hegiht_ratio)
        undercut_height = tree_height*undercut_hegiht_ratio

        # scale
        shape_section_coordinates = [(p[0]*canopy_radius,p[1]*canopy_height+undercut_height) for p in base_coordinates]
        return shape_section_coordinates


    @classmethod
    def get_height_category(cls,height):
        # find a height category that is equal or lower to the height 
        return next(h for h in cls.__config.tree_height_category if int(floor(height))<=h)
    

    @property
    def is_placed(self):
        return (not self.is_damy) and (self.placed_cell is not None)


    @property
    def diameter(self):
        return self.DH_ratio * self.__height

    @property
    def radius(self):
        return self.estimate_radius_from_height(self.__height)
    
    @property
    def root_radius(self):
        return self.__root_radius
    
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
            new.is_damy = False
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
    

        


    
    def matches_cell_environment(self,testing_cell,log=None):
        """Check if this tree can be planted in the testing cell.

        Parameters
        ----------
        testing_cell : Cell

        Returns
        -------
        is_placable: bool
        status: str
        """
        if testing_cell.sunshine_duration < self.required_shade_tolerance:
            return False,"sunshine duration is too short"
        # check wind speed
        elif testing_cell.wind_speed > self.limit_wind_tolerance:
            return False,"wind speed is too fast"
        # check soil thickness
        elif testing_cell.soil_thickness < self.required_soil_thickness:
            return False,"soil thickness is too thin"
        # check distance to edge
        elif testing_cell.distance_to_edge < self.safety_distance:
            return False,"too close to edge"
        else:
            # default
            return True,"ok"
        
    def checks_root_collision(self,other_tree,self_tree_origin=None):
        if self_tree_origin is None and self.point is None: # other tree has been set = must have point attribute.
            raise Exception("To check root collision, self and other trees must already have been placed.\nYou can specify damy origin for self via the parameter 'self_tree_origin'.\n self.placed_cell: {}\nother_tree.placed_cell: {}".format(self.placed_cell,neighbor.placed_cell)) # type:ignore
        self_point = self_tree_origin or self.point
        xy_dist_square = (other_tree.point.X - self_point.X)**2 +(other_tree.point.Y - self_point.Y)**2 # type: ignore
        required_dist = (self.safety_distance+other_tree.safety_distance)**2
        return xy_dist_square>=required_dist
                
    
    def get_overlapping_ratio(self,neighbor_trees,self_tree_origin=None):
        """_summary_

        Parameters        ----------
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
        
        if self_tree_origin is None and self.point is None: # other tree has been set = must have point attribute.
            raise Exception("To compute canopy overlapping area, self and other trees must already have been placed.\nYou can specify damy origin for self via the parameter 'self_tree_origin'.\n self.placed_cell: {}\nother_tree.placed_cell: {}".format(self.placed_cell,neighbor.placed_cell)) # type:ignore

        self_point = self_tree_origin or self.point

        # find overlapped trees and its intersectioned area
        overlap_neighbors = []
        intersected_area = 0.0
        self_tree_section,self_tree_area = self.get_tree_shape_info()

        for neighbor in neighbor_trees:
            xy_dist = (
                    (neighbor.point.X - self_point.X)**2 # type: ignore
                   +(neighbor.point.Y - self_point.Y)**2 # type: ignore
                )**(1.0/2.0)
            z_dist = neighbor.point.Z - self_point.Z # type: ignore
            vec = (xy_dist,z_dist)

            other_tree_section = neighbor.get_tree_shape_info()[0]
            other_tree_shape_section_translated = translate_coordinates(other_tree_section,vec)
            overlap_region_as_pathsD = PolylineBoolenCalculation.intersect_polyline(pl1=self_tree_section,
                                                                                    pl2=other_tree_shape_section_translated,
                                                                                    use_rhino=False,
                                                                                    return_clipper_path=True)
            if overlap_region_as_pathsD.Count>0: #type: ignore
                for pathD in overlap_region_as_pathsD:
                    intersected_area += PolylineBoolenCalculation.get_area_of_clipper_path(pathD)
                overlap_neighbors.append(neighbor)
        
        overlap_ratio = intersected_area / self_tree_area
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
        if not self.is_placed: raise Exception("Only placed trees can be rechecked.")

        added_tree = extra_tree.get_damy_pointed_tree(extra_tree_origin)
        overlapped_trees = self.overlapped_trees
        overlapped_trees.append(added_tree)

        ov_ratio,_ = self.get_overlapping_ratio(overlapped_trees)
        
        return ov_ratio<=self.placed_cell.FD_overlap_tolerance_ratio # type:ignore






    @classmethod
    def generate_trees_from_database(cls,database_matrix):
        args_col_names = {
            "species":cls.__config.tree_asset_table_col_species,
            "symbol":cls.__config.tree_asset_table_col_symbol,
            "height":cls.__config.tree_asset_table_col_height,
            "trunk_circumference":cls.__config.tree_asset_table_col_trunk_circumference,
            "diameter":cls.__config.tree_asset_table_col_diameter,
            "root_diameter":cls.__config.tree_asset_table_col_root_diameter,
            "safety_distance":cls.__config.tree_asset_table_col_safety_distance,
            "maximum_height":cls.__config.tree_asset_table_col_maximum_height,
            "shade_tolerance":cls.__config.tree_asset_table_col_shade_tolerance,
            "wind_tolerance":cls.__config.tree_asset_table_col_wind_tolerance,
            "shape_type":cls.__config.tree_asset_table_col_shape_type,
            "root_type":cls.__config.tree_asset_table_col_root_type,
            "growing_speed":cls.__config.tree_asset_table_col_growing_speed,
            "is_evergreen":cls.__config.tree_asset_table_col_is_evergreen,
            "is_conifers":cls.__config.tree_asset_table_col_is_conifers,
            "undercut_height_ratio":cls.__config.tree_asset_table_col_undercut_height_ratio,
            "growing_parameter_B":cls.__config.tree_asset_table_col_growign_parameter_B,
            "growing_parameter_k":cls.__config.tree_asset_table_col_growign_parameter_k
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