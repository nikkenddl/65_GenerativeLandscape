from copy import deepcopy
from itertools import chain
from collections import defaultdict
from .config import Config
from .rhinopy import PointableRTree


class Analyser(object):
    _config = Config()
    def __init__(self,placed_cells):
        self._cells = placed_cells
        self._cell_dict = None
        self._cell_matrix = None


    def evaluate(self,key):
        cells = []
        region_eval_values = []
        region_error_values = []
        region_comment = []
        tree_eval_values = []
        tree_error_values = []
        tree_comment = []

        key = str(key).lower()

        if key in RegionAnalyser.class_keys:
            analyser = RegionAnalyser.__new__(RegionAnalyser)
            analyser._cells = self._cells
            cells,trees,tree_states,region_eval_values,region_error_values = analyser._evaluate(key)
        elif key in RelationAnalyser.class_keys:
            analyser = RelationAnalyser.__new__(RelationAnalyser)
            analyser._cells = self._cells
            trees,tree_states,tree_eval_values,tree_error_values,tree_comment = analyser._evaluate(key)
        elif key in TreeAnalyser.class_keys:
            analyser = TreeAnalyser.__new__(TreeAnalyser)
            analyser._cells = self._cells
            trees,tree_states,tree_eval_values,tree_error_values,tree_comment = analyser._evaluate(key)
        else:
            raise Exception("key-{} is not contained in any analyser".format(key))
        
        return (cells,
                trees,
                region_eval_values,
                region_error_values,
                region_comment,
                tree_states,
                tree_eval_values,
                tree_error_values,
                tree_comment)


    def _set_cell_dict(self):
        self._cell_dict = {c.ID:c for c in self._cells}

    def _set_cell_matrix(self):
        self._cell_matrix = self.cell_chain_to_matrix(self._cells)

    @staticmethod
    def cell_chain_to_matrix(cells):
        numerical_grid = cells[0].grid_info
        xnum,ynum = numerical_grid.x_num,numerical_grid.y_num
        matrix = [[None]*xnum for _ in range(ynum)]
        for c in cells:
            x,y = c.xy_ID
            matrix[y][x] = c
        return matrix
    

class RegionAnalyser(Analyser):
    class_keys = ("dominant","density","egdd")
    def __init__(self, placed_cells):
        super(RegionAnalyser,self).__init__(placed_cells)


    def _split_by_forest_regions(self):
        # region_ID_matrix = [[c.forest_region.ID+1 if c else 0 for c in row] for row in self.__cell_matrix]
        # cc = ConnectedComponents(region_ID_matrix,True)
        # label = cc.find_components()

        # label = [l for l in chain.from_iterable(label) if l]
        # regions = defaultdict(list)

        # for l,c in zip(label,self._cells):
        #     regions[l].append(c)

        # return regions

        regions = defaultdict(list)

        for c in self._cells:
            regions[c.forest_region.ID].append(c)
        
        return regions


    def _evaluate(self,key):
        rst = None
        key = str(key).lower()

        if key=="dominant":
            rst = self.evaluate_dominants()
        elif key=="density":
            rst = self.evaluate_density()
        elif key=="egdd":
            rst = self.evaluate_EGDD()
        else:
            raise Exception("key-{} is not interplemented".format(key))

        return rst
    

    def evaluate_dominants(self):
        cells_by_regions = [ls for ls in self._split_by_forest_regions().values()]

        eval_values = []
        trees = []
        tree_states = []
        tol = self._config.dominant_species_ratio

        for cells in cells_by_regions:
            assert cells
                
            dominant_species = cells[0].FD_dominant_species
            if not dominant_species:
                eval_values.append(None)
                continue

            trees_in_region = [c.placed_tree for c in cells if c.placed_tree]
            if not trees_in_region:
                # not trees are placed in the region
                eval_values.append(None)
                continue

            trees.extend(trees_in_region)

            is_dominant = [t.species in dominant_species for t in trees_in_region]
            count_dominant = sum(is_dominant)

            tree_states.extend(is_dominant)

            dominant_ratio = float(count_dominant)/float(len(trees_in_region))
            eval_values.append(dominant_ratio)

        error_values = [ev-tol if ev else 0.0 for ev in eval_values]

        # to persentage
        eval_values = [e*100 for e in eval_values]
        error_values = [e*100 for e in error_values]
        
        return (cells_by_regions,trees,tree_states,eval_values,error_values)




    def evaluate_density(self):
        cells_by_regions = [ls for ls in self._split_by_forest_regions().values()]

        eval_values = []
        error_values = []
        trees = []

        for cells in cells_by_regions:
            assert cells
                
            tol = cells[0].forest_region.forest_domain.density * 100 * 1000000 # to tree per 100m2
            area = cells[0].forest_region.area

            trees_in_region = [c.placed_tree for c in cells if c.placed_tree]
            tree_count = len(trees_in_region)

            density = tree_count / area * 100 * 1000000 # to tree per 100m2
            error = density - tol
            
            trees.extend(trees_in_region)
            eval_values.append(density)
            error_values.append(error)

        tree_states = [True] * len(trees)
        
        return (cells_by_regions,trees,tree_states,eval_values,error_values)


    def evaluate_EGDD(self):
        cells_by_regions = [ls for ls in self._split_by_forest_regions().values()]

        eval_values = []
        error_values = []
        trees = []
        tree_states = []

        for cells in cells_by_regions:
            assert cells
                
            tol = cells[0].FD_eg_ratio * 100 # to persentage

            trees_in_region = [c.placed_tree for c in cells if c.placed_tree]
            if not trees_in_region:
                # not trees are placed in the region
                eval_values.append(None)
                error_values.append(None)
                continue

            is_eg = [t.is_evergreen for t in trees_in_region]
            count_eg = sum(is_eg)

            density = float(count_eg) / float(len(trees_in_region)) * 100# to pesentage
            error = density - tol
            
            trees.extend(trees_in_region)
            tree_states.extend(is_eg)
            eval_values.append(density)
            error_values.append(error)
        
        return (cells_by_regions,trees,tree_states,eval_values,error_values)

class RelationAnalyser(Analyser):
    class_keys = ("overlap","layer")
    def __init__(self,placed_cells):
        super(RelationAnalyser,self).__init__(placed_cells)

    
    def _evaluate(self,key):
        rst = None
        key = str(key).lower()

        if key=="overlap":
            rst = self.evaluate_overlap()
        elif key=="layer":
            rst = self.evaluate_layer()
        else:
            raise Exception("key-{} is not interplemented".format(key))

        return rst
    

    def evaluate_overlap(self):
        cells_has_tree = [c for c in self._cells if c.placed_tree]
        trees = [c.placed_tree for c in cells_has_tree]

        eval_values = []
        error_values = []
        tree_states = []
        com = []

        for c in cells_has_tree:
            tree = c.placed_tree

            tol = c.FD_overlap_tolerance_ratio

            overlapped_neighbors = tree.overlapped_trees
            ov_ratio,_ = tree.get_overlapping_ratio(overlapped_neighbors)

            err = ov_ratio - tol

            # to persentage
            ov_ratio *= 100
            err *= 100

            eval_values.append(ov_ratio)
            error_values.append(err)
            tree_states.append(err<=0)
        
        return (trees,tree_states,eval_values,error_values,com)


    def evaluate_layer(self):
        cells_has_tree = [c for c in self._cells if c.placed_tree]
        trees = [c.placed_tree for c in cells_has_tree]

        eval_values = []
        error_values = []
        tree_states = []
        com = []

        rtree = PointableRTree(trees)
        dist = self._config.radius_to_check_forest_layer_count

        com_fmt = "H_cat:{}"


        for c in cells_has_tree:
            tree = c.placed_tree

            tol = c.FD_vicinity_same_height_category_limit

            neighbors = rtree.search_close_objects(tree,dist)
            height_classes = set(t.height_category for t in neighbors)

            layer_count = len(height_classes)
            err = layer_count - tol

            eval_values.append(layer_count)
            error_values.append(err)
            tree_states.append(err<=0)

            com.append(com_fmt.format(len(neighbors)))
        
        return (trees,tree_states,eval_values,error_values,com)
            

class TreeAnalyser(Analyser):
    class_keys = ("sunshine_duration","wind_speed","soil_thickness")
    def __init__(self,placed_cells):
        super(TreeAnalyser,self).__init__(placed_cells)

    def _evaluate(self,key):
        rst = None
        key = str(key).lower()

        if key=="sunshine_duration":
            rst = self.evaluate_sunshine_duration()
        elif key=="wind_speed":
            rst = self.evaluate_wind_speed()
        elif key=="soil_thickness":
            rst = self.evaluate_soil_thickness()
        else:
            raise Exception("key-{} is not interplemented".format(key))

        return rst
    

    def evaluate_sunshine_duration(self):
        cells_has_tree = [c for c in self._cells if c.placed_tree]

        trees = []
        tree_states = []
        eval_values = []
        error_values = []
        com = []

        for c in cells_has_tree:
            tree = c.placed_tree
            sun_duration_hour = c.sunshine_duration
            tol = tree.required_shade_tolerance
            err = sun_duration_hour - tol
            state = err>=0

            trees.append(tree)
            tree_states.append(state)
            eval_values.append(sun_duration_hour)
            error_values.append(err)
        
        return (trees,tree_states,eval_values,error_values,com) 
    
    def evaluate_wind_speed(self):
        cells_has_tree = [c for c in self._cells if c.placed_tree]

        trees = []
        tree_states = []
        eval_values = []
        error_values = []
        com = []

        for c in cells_has_tree:
            tree = c.placed_tree
            wind_speed = c.wind_speed
            tol = tree.limit_wind_tolerance
            err = wind_speed - tol
            state = err<=0

            trees.append(tree)
            tree_states.append(state)
            eval_values.append(wind_speed)
            error_values.append(err)
        
        return (trees,tree_states,eval_values,error_values,com) 
    

    def evaluate_soil_thickness(self):
        cells_has_tree = [c for c in self._cells if c.placed_tree]

        trees = []
        tree_states = []
        eval_values = []
        error_values = []
        com = []

        for c in cells_has_tree:
            tree = c.placed_tree
            soil_thickness = c.soil_thickness
            tol = tree.required_soil_thickness
            err = soil_thickness - tol
            state = err>=0

            trees.append(tree)
            tree_states.append(state)
            eval_values.append(soil_thickness)
            error_values.append(err)
        
        return (trees,tree_states,eval_values,error_values,com) 




class ConnectedComponents:
    def __init__(self, matrix, set_to_adjacency_4):
        self.matrix = matrix
        if len(set(len(row) for row in matrix))!=1:
            raise Exception("matrix must be rectangular")
        
        self.rows = len(matrix)
        self.cols = len(matrix[0]) if self.rows > 0 else 0
        self.labels = None
        self.visited = None
        self.directions = None
        self.set_mode(set_to_adjacency_4)
        

    def is_valid(self, x, y, searching_value):
        return (0 <= x < self.rows and
                0 <= y < self.cols and
                not self.visited[x][y] and
                self.matrix[x][y] == searching_value)

    def explore(self, x, y, label, searching_value):
        if self.visited[x][y]:
            return
        self.visited[x][y] = True
        self.labels[x][y] = label
        
        for dx, dy in self.directions:
            new_x, new_y = x + dx, y + dy
            if self.is_valid(new_x, new_y, searching_value):
                self.explore(new_x, new_y, label, searching_value)

    def find_components(self):
        label = 1
        self.labels = [[0] * self.cols for _ in range(self.rows)]
        self.visited = [[False] * self.cols for _ in range(self.rows)]
        for i in range(self.rows):
            for j in range(self.cols):
                searching_value = self.matrix[i][j]
                if searching_value != 0 and not self.visited[i][j]:
                    self.explore(i, j, label, searching_value)
                    label += 1
        return deepcopy(self.labels)
        
    def set_mode(self,set_to_adjacency_4):
        self.directions = [(-1, 0), (1, 0), (0, -1), (0, 1)] # for 4-Adjacency
        if not set_to_adjacency_4:
            self.directions += [(-1, -1), (-1, 1), (1, -1), (1, 1)] # add diagonals for 8-Adjacency