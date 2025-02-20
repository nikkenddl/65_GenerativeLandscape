from .config import Config

class Cell:
    __config = Config()
    __FD_DICT = {}
    __FR_DICT = {}
    __NumericalGrid = None

    def __init__(self,
                 ID,
                 point,
                 forest_region,
                 soil_thickness,
                 wind_speed,
                 sunshine_duration,
                 distance_to_edge):
        self.ID = int(ID)
        self.point = point
        self.forest_region = forest_region
        self.FDname = str(self.forest_region.forest_domain.name)
        self.soil_thickness = int(soil_thickness)
        self.wind_speed = float(wind_speed)
        self.sunshine_duration = float(sunshine_duration)
        self.distance_to_edge = float(distance_to_edge)

        self.placed_tree = None
        self.__is_killed = False

        self.forest_region.cells.append(self)

        self.tree_height_limit = self.get_height_limit_by_soil_thickness(self.soil_thickness)

    def clear(self):
        self.placed_tree=None
        self.__is_killed = False

    
    @classmethod
    def set_grid_info(cls,origin,x_count,y_count,span):
        cls.__NumericalGrid = NumericalGrid(grid_origin=origin,
                                            cell_span=span,
                                            num_cells_x=x_count,
                                            num_cells_y=y_count)
        
    @classmethod
    def get_cell_ID_of_point(cls,point):
        assert cls.__NumericalGrid
        id_,_,_ =  cls.__NumericalGrid.index_at_point(point,-1)
        if id_==-1:
            raise Exception("inputted point is out of grid. inputted point : {}".format(point))
        return id_


    @classmethod
    def get_height_limit_by_soil_thickness(cls,thickness):
        thickness_category = next(thcat for thcat in cls.__config.soil_thickness_category if thickness>=thcat)
        return float(cls.__config.height_limit_by_soil_thickness_category[thickness_category])
        

    @staticmethod
    def create_from_map_info(ID_list,
                             point_list,
                             sunshine_duration_list,
                             soil_thickness_list,
                             wind_speed_list,
                             forest_region_id_list,
                             forest_regions,
                             distance_to_edge_list
                             ):
        assert all(len(ID_list)==len(l) for l in [point_list,
                                                  sunshine_duration_list,
                                                  soil_thickness_list,
                                                  wind_speed_list,
                                                  forest_region_id_list,
                                                  distance_to_edge_list])
        cells = [None] * len(ID_list)
        invalid_cell_points = []
        count = 0
        fr_dict = {fr.ID:fr for fr in forest_regions}
        
        for ID,pt,sd,st,ws,frid,de in zip(ID_list,
                                          point_list,
                                          sunshine_duration_list,
                                          soil_thickness_list,
                                          wind_speed_list,
                                          forest_region_id_list,
                                          distance_to_edge_list):
            if ID is not None\
           and pt is not None\
           and sd is not None\
           and st is not None\
           and ws is not None\
           and frid is not None\
           and de is not None:
                fr = fr_dict[frid]
                cells[count] = Cell(ID=ID,
                                    point=pt,
                                    forest_region=fr,
                                    soil_thickness=st,
                                    wind_speed=ws,
                                    sunshine_duration=sd,
                                    distance_to_edge=de)
                count+=1
            else:
                invalid_cell_points.append(pt)

        cells = cells[:count]
        return cells,invalid_cell_points
    
    @property
    def is_dead(self):
        return self.__is_killed or\
            self.placed_tree is not None\
            or self.forest_region.has_finished_placement
    
    @property
    def xy_ID(self):
        """return col and row index of the cell.

        Returns
        -------
        (x,y) (2,) int
        """
        y,x = divmod(self.ID,self.__NumericalGrid.x_num)
        return (int(x),int(y))
    
    def kill(self):
        self.__is_killed = True

    @classmethod
    def set_FD(cls, FD):
        cls.__FD_DICT[FD.name] = FD

    @classmethod
    def set_FDs(cls, FDs):
        for FD in FDs:
            cls.set_FD(FD)

    @classmethod
    def set_FR(cls, FR):
        cls.__FR_DICT[FR.ID] = FR

    @classmethod
    def set_FRs(cls, FRs):
        for FR in FRs:
            cls.set_FR(FR)

    @property
    def grid_info(self):
        return self.__NumericalGrid

    
    @property
    def FD_density(self):
        if self.FDname not in self.__FD_DICT: raise Exception("FD has not been set yet")
        return self.__FD_DICT[self.FDname].density
    
    @property
    def FD_overlap_tolerance_ratio(self):
        if self.FDname not in self.__FD_DICT: raise Exception("FD has not been set yet")
        return self.__FD_DICT[self.FDname].overlap_tolerance_ratio
    
    @property
    def FD_vicinity_same_height_category_limit(self):
        if self.FDname not in self.__FD_DICT: raise Exception("FD has not been set yet")
        return self.__FD_DICT[self.FDname].vicinity_same_height_category_limit
    
    @property
    def FD_eg_ratio(self):
        if self.FDname not in self.__FD_DICT: raise Exception("FD has not been set yet")
        return self.__FD_DICT[self.FDname].eg_ratio
    
    @property
    def FD_eg_ratio_in_gap(self):
        if self.FDname not in self.__FD_DICT: raise Exception("FD has not been set yet")
        return self.__FD_DICT[self.FDname].eg_ratio_in_gap
    
    @property
    def FD_gap_size(self):
        if self.FDname not in self.__FD_DICT: raise Exception("FD has not been set yet")
        return self.__FD_DICT[self.FDname].gap_size
    
    @property
    def FD_dominant_species(self):
        if self.FDname not in self.__FD_DICT: raise Exception("FD has not been set yet")
        return self.__FD_DICT[self.FDname].dominant_species
    
    def __str__(self):
        return "Cell<{}>".format(self.ID)
    
    def __eq__(self, other):
        if not isinstance(other, Cell):
            return False
        return self.ID == other.ID

    def __hash__(self):
        return hash(self.ID+11093)
    

class NumericalGrid:
    def __init__(self,grid_origin, cell_span, num_cells_x, num_cells_y):
        if cell_span<1: raise Exception("Span is too small")
        if grid_origin is None\
        or not num_cells_x\
        or not num_cells_y\
        or not cell_span:
            raise Exception("Some parameters are wrong")
        self.span = cell_span
        self.x_interval = (grid_origin.X,grid_origin.X + self.span * num_cells_x)
        self.y_interval = (grid_origin.Y,grid_origin.Y + self.span * num_cells_y)
        self.x_num = int(num_cells_x)
        self.y_num = int(num_cells_y)

    def index_at_point(self,point, not_found_value=-1):
        """Inspect grid face index at a point
        
        Parameters
        ----------
        point : Rhino.Geometry.Point3d | Rhino.Geometry.Point2d
        """
        x, y = point.X, point.Y

        # point is outside of grid
        if x < self.x_interval[0]\
        or y < self.y_interval[0]\
        or x >= self.x_interval[1]\
        or y >= self.y_interval[1]:
            return (not_found_value,None,None)

        cell_x = int((x - self.x_interval[0]) / self.span)
        cell_y = int((y - self.y_interval[0]) / self.span)

        # get index if the cell list is 1d list.
        index = cell_y * self.x_num + cell_x

        return (index,cell_x,cell_y)