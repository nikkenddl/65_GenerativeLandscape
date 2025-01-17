class Cell:
    __FD_DICT = {}

    def __init__(self,
                 ID,
                 point,
                 forest_region,
                 soil_thickness,
                 wind_speed,
                 sunshine_duration):
        self.ID = int(ID)
        self.point = point
        self.forest_region = forest_region
        self.FDname = self.forest_region.forest_domain.name
        self.soil_thickness = soil_thickness
        self.wind_speed = wind_speed
        self.sunshine_duration = sunshine_duration

        self.placed_tree = None
        self.__is_killed = False

        self.forest_region.cells.append(self)

    def clear(self):
        self.placed_tree=None

    @staticmethod
    def create_from_map_info(ID_list,
                             point_list,
                             sunshine_duration_list,
                             soil_thickness_list,
                             wind_speed_list,
                             forest_region_id_list,
                             forest_regions
                             ):
        assert all(len(ID_list)==len(l) for l in [point_list,sunshine_duration_list,soil_thickness_list,wind_speed_list,forest_region_id_list])
        cells = [None] * len(ID_list)
        invalid_cell_points = []
        count = 0
        fr_dict = {fr.ID:fr for fr in forest_regions}
        
        for ID,pt,sd,st,ws,frid in zip(ID_list,point_list,sunshine_duration_list,soil_thickness_list,wind_speed_list,forest_region_id_list):
            if ID is not None\
           and pt is not None\
           and sd is not None\
           and st is not None\
           and ws is not None\
           and frid is not None:
                fr = fr_dict[frid]
                cells[count] = Cell(ID=ID,
                                    point=pt,
                                    forest_region=fr,
                                    soil_thickness=st,
                                    wind_speed=ws,
                                    sunshine_duration=sd)
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
    
    def kill(self):
        self.__is_killed = True

    @classmethod
    def set_FD(cls, FD):
        cls.__FD_DICT[FD.name] = FD

    @classmethod
    def set_FDs(cls, FDs):
        for FD in FDs:
            cls.set_FD(FD)
    
    @property
    def FD_density(self):
        if self.FDname not in self.__FD_DICT: raise Exception("FD has not been set yet")
        return self.__FD_DICT[self.FDname].density
    
    @property
    def FD_overlap_tolerance_ratio(self):
        if self.FDname not in self.__FD_DICT: raise Exception("FD has not been set yet")
        return self.__FD_DICT[self.FDname].overlap_tolerance_ratio
    
    @property
    def FD_count_top_layer_species(self):
        if self.FDname not in self.__FD_DICT: raise Exception("FD has not been set yet")
        return self.__FD_DICT[self.FDname].count_top_layer_species
    
    @property
    def FD_eg_dd_ratio(self):
        if self.FDname not in self.__FD_DICT: raise Exception("FD has not been set yet")
        return self.__FD_DICT[self.FDname].eg_dd_ratio
    
    @property
    def FD_eg_dd_ratio_in_gap(self):
        if self.FDname not in self.__FD_DICT: raise Exception("FD has not been set yet")
        return self.__FD_DICT[self.FDname].eg_dd_ratio_in_gap
    
    @property
    def FD_gap_size(self):
        if self.FDname not in self.__FD_DICT: raise Exception("FD has not been set yet")
        return self.__FD_DICT[self.FDname].gap_size
    
    @property
    def FD_dominant_species(self):
        if self.FDname not in self.__FD_DICT: raise Exception("FD has not been set yet")
        return self.__FD_DICT[self.FDname].dominant_species
    
    def __eq__(self, other):
        if not isinstance(other, Cell):
            return False
        return self.ID == other.ID

    def __hash__(self):
        return hash(self.ID+11093)