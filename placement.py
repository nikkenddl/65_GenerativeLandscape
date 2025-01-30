import random
from collections import Iterable,defaultdict
from .rhinopy import PointableRTree
from .config import Config

from time import time

class ForestCreator:
    __config = Config()
    def __init__(self,
                 cell_altanatives,
                 tree_altanatives,
                 placement_postponed_trees=[],
                 limit_iteration=50,
                 random_seed=65):
        try: random.seed(random_seed, version=1)  # Python 3
        except TypeError: random.seed(random_seed)  # Python 2
        s = time()
        self.clear_cells(cell_altanatives)
        print('time to clear cell: {}'.format(time()-s))
        
        self.__CELL_FINDING_LIMIT_DISTANCE = 20000.0
        s = time()
        self.cell_states = {cell : self.__CELL_FINDING_LIMIT_DISTANCE for cell in cell_altanatives}
        print('time to init cell state: {}'.format(time()-s))

        self.trees = tree_altanatives
        
        self.__failured_count = 0
        self.__limit_failured_count = int(limit_iteration)
        self.__placed_trees = []

        self.preplaced_unplaced_trees = []

        s = time()
        self.all_cell_rtree = PointableRTree(cell_altanatives)
        print('time to init all_cell_rtree: {}'.format(time()-s))

        self.placed_tree_rtree = PointableRTree([])

        s = time()
        self.init_preplaced(placement_postponed_trees)
        print('time to init preplaced trees: {}'.format(time()-s))
        


    def clear_cells(self,cells):
        s = time()
        for c in cells:
            c.clear()
        print('time to clear cell : {}'.format(time()-s))
        s = time()
        frs = set(c.forest_region for c in cells)
        print('time to create set of forest regions : {}'.format(time()-s))
        s = time()
        for fr in frs:
            fr.initialize()
        print('time to init forest regions: {}'.format(time()-s))
        print('count of forest region: {}'.format(len(frs)))


    def init_preplaced(self,placement_postponed_trees):
        """Update placement status by preplaced trees.

        Parameters
        ----------
        placement_postponed_trees : (n,) PlacementPostponedTree
        """
        for ppt in placement_postponed_trees:
            placed = ppt.place()
            if placed:
                self.update_state(placed)
            else:
                self.preplaced_unplaced_trees.append(ppt.place_damy())
            

        
    def create(self):
        __time_to_pick_cell = []
        __time_to_try_to_place = []
        __time_to_update_state = []
        __failured_status = []
        # for _ in range(10):
        while not self.is_created:
            # if self.is_created: break
            s = time()
            testing_cell = self.pick_cell()
            __time_to_pick_cell.append(time()-s)
            assert testing_cell is not None

            s = time()
            placed_tree,status = self.try_to_place(testing_cell)
            __time_to_try_to_place.append(time()-s)
            if placed_tree:
                self.__failured_count = 0
                s = time()
                self.update_state(placed_tree)
                __time_to_update_state.append(time()-s)
            else:
                __failured_status.append(status)
                self.__failured_count += 1
                testing_cell.kill()
                del self.cell_states[testing_cell]

        def print_summary(elapsed_time_list,title):
            print("\nelapsed time[s] for {}\n--------".format(title))
            total = sum(elapsed_time_list)
            cnt = len(elapsed_time_list)
            average = 0 if cnt==0 else total/cnt
            print("total : {}".format(total))
            print("average : {}".format(average))
            print("count : {}".format(cnt))
            print('\n')
        def try_write_log_files(txt,file_name_without_extension):
            try:
                with open(r"D:\Users\11104\Desktop\{}.txt".format(file_name_without_extension),'w') as f:
                    f.write(txt)
            except Exception as e:
                print('failured writing log.\n{}'.format(e))

        print_summary(__time_to_pick_cell,'TIME_TO_PICK_CELL')
        print_summary(__time_to_try_to_place,'TIME_TO_TRY_TO_PLACE')
        print_summary(__time_to_update_state,'TIME_TO_UPDATE_STATE')
        try_write_log_files("\n".join(__failured_status),"failured_status")
        return self.__placed_trees

    @property
    def is_created(self):
        # too many failured.
        if self.__failured_count>=self.__limit_failured_count: return True
        # tree counts is enough for all region => all cells are removed.
        if len(self.cell_states)==0: return True

        # default
        return False
    
    def pick_cell(self):
        farthest_dist = -float('inf')
        farthest_cell = None
        for cell,dist in self.cell_states.items():
            if dist>=self.__CELL_FINDING_LIMIT_DISTANCE:
                farthest_cell = cell
                break
            if dist>farthest_dist:
                farthest_cell = cell
                farthest_dist = dist
        return farthest_cell

    
    def try_to_place(self,cell):
        filtered_trees,status = self.filtering(cell)
        if not filtered_trees:
            return None,status
        possibility = self.possibility(filtered_trees,cell)
        placed_tree,status = self.placement(filtered_trees,possibility,cell)
        return placed_tree,status
            
    def filtering(self,cell):
        """Filtering trees by cell situation.

        Parameters
        ----------
        cell : Cell

        Returns
        -------
        filtered_trees: (n,) Tree
        """
        def count_defaultdict(it):
            counter = defaultdict(int)
            for x in it:
                counter[x] += 1
            return dict(counter)
        # filter trees with environment
        ls_is_cleared = [t.matches_cell_environment(cell) for t in self.trees]

        
        if not (any(rst[0] for rst in ls_is_cleared)):
            statuses = [rst[1] for rst in ls_is_cleared]
            counter = count_defaultdict(statuses)
            most_status = max(counter.items(),key=lambda it: it[1])[0]
            return [],most_status
        trees_matches_environment = [t for t,rst in zip(self.trees,ls_is_cleared) if rst[0]]
        
       
       # filter trees by tree layer count limit.
        close_placed_trees = self.placed_tree_rtree.search_close_objects(cell,self.__config.radius_to_check_forest_layer_count)
        limit_layer_count = cell.FD_vicinity_same_height_category_limit

        if len(close_placed_trees)<limit_layer_count:
            # close placed tree count less than limit. = any height category trees can be placed.
            pass
        else:
            # Placed and closed tree count is equal or larger than limit count. 
            # Filter the placing trees, keeping only those with
            # a height category that matches the height categories of nearby placed trees.
            height_category_in_vicinity = set(t.height_category for t in close_placed_trees)
            if len(height_category_in_vicinity)>=limit_layer_count:
                trees_matches_environment = [t for t in self.trees if t.height_category in height_category_in_vicinity]
        

        return trees_matches_environment,"OK"
    
    
    def possibility(self,trees,cell):
        L = len(trees)
        possibility_list = [1.0] * L

        # possiblity by dominant species
        dominant_species = cell.FD_dominant_species
        are_dominant = [t.species in dominant_species for t in trees]
        count_dominant = sum(are_dominant)
        count_undominant = L-count_dominant
        
        if count_dominant==0 or count_undominant==0:
            pass # do nothing
        else:
            dominant_possibility = 0.7/float(count_dominant)
            undominant_possibility = 0.3/float(count_undominant)
            for i in range(L):
                if are_dominant[i]:
                    possibility_list[i] *= dominant_possibility
                else:
                    possibility_list[i] *= undominant_possibility

        # possibility by ratio of evergreen and diciduous
        eg_ratio = cell.FD_eg_ratio
        dd_ratio = 1.0 - eg_ratio
        are_EG = [t.is_evergreen for t in trees]
        count_EG = sum(are_EG)
        count_DD = L-count_EG

        if count_EG==0 or count_DD==0:
            pass # do nothing
        else:
            eg_possibility = eg_ratio/float(count_EG)
            dd_possibility = dd_ratio/float(count_DD)
            for i in range(L):
                if are_EG[i]:
                    possibility_list[i] *= eg_possibility
                else:
                    possibility_list[i] *= dd_possibility

        return possibility_list
    
    
    def placement(self,tree_altanatives,weight,cell):
        def weighted_choice(choices, weights, n_extract=-1):
            """extract elements from list. Extraction possibility is weighted by weights.
            """
            n_extract = int(n_extract)
            if n_extract<0:
                n_extract = len(choices)
            elif n_extract>len(choices):
                n_extract = len(choices)

            # compute cumulative weights.
            cumulative_weights = []
            current_sum = 0
            for weight in weights:
                current_sum += weight
                cumulative_weights.append(current_sum)

            # result archive
            sorted_choices = []

            # loop until n_extract elements are extracted.
            for _ in range(n_extract):
                # generate random float value bet. 0 to sum of weight
                random_num = random.uniform(0, cumulative_weights[-1])

                # choose
                for i, cumulative_weight in enumerate(cumulative_weights):
                    if random_num <= cumulative_weight:
                        # add choosen element
                        sorted_choices.append(choices[i])

                        # set 0 to possibility of choosen element.
                        weight_to_remove = weights[i]
                        weights[i] = 0

                        # update culmative weight before choosen.
                        for j in range(i, len(cumulative_weights)):
                            cumulative_weights[j] -= weight_to_remove

                        break
                    
            return sorted_choices
        
        if not tree_altanatives: 
            # print('No placable tree')
            return None,"no inputted tree"
        # tree = random.choices(tree_altanatives,weight)[0]
        # tree = random.choice(tree_altanatives)
        tree = weighted_choice(tree_altanatives,weight,1)[0]
        overlapping_neighbors=[]

        # add collision check here
        close_placed_trees = self.placed_tree_rtree.search_close_objects(cell,self.__config.radius_to_check_collision)
        if close_placed_trees:
            overlapping_ratio,overlapping_neighbors = tree.get_overlapping_ratio(close_placed_trees,cell.point)
            if overlapping_ratio<=cell.FD_overlap_tolerance_ratio:
                # placing tree's overlap is acceptable.
                # But neighbors overlap ratio is unknown, recheck their overlapping ratio.
                results_is_acceptable = [t.recheck_overlap(tree,cell.point) for t in overlapping_neighbors]
                if all(results_is_acceptable):
                    # All neighbors' overlap is acceptable.
                    pass
                else:
                    # The tree whose overlapping ratio exceeds the tolerance if the placing tree is placed.
                    return None,"Already placed trees whose overlapping ratio exceeds the tolerance"
            else:
                # too close with already placed tree.
                return None,"Placing Tree is too close with already placed trees"

        # place tre trying tree
        placed_tree = tree.place(cell)
        placed_tree.register_overlapped_trees(overlapping_neighbors)

        # Register the placed tree as an overlapped tree with neighbours.
        for neighbor in overlapping_neighbors:
            neighbor.register_overlapped_tree(placed_tree)

        return placed_tree,"OK"
        
    
    def update_state(self,placed_tree):
        # register the placed tree to cache
        self.__placed_trees.append(placed_tree)
        self.placed_tree_rtree.append(placed_tree)

        if any(cell.is_dead for cell in self.cell_states.keys()):
            # if some cells can't be used.
            #   - ForestRegion of cell is fullfilled
            self.cell_states = {cell:dist for cell,dist in self.cell_states.items()
                                    if not cell.is_dead}

        placed_point = placed_tree.point
        radius = placed_tree.radius
        assert placed_point is not None

        # update only closer cells
        close_cells_set = self.all_cell_rtree.search_close_objects(placed_tree,self.__CELL_FINDING_LIMIT_DISTANCE)

        for cell in close_cells_set:
            if cell not in self.cell_states:
                continue
            new_d = cell.point.DistanceTo(placed_point)-radius

            if new_d<self.cell_states[cell]: # if new placed tree is closer than others
                self.cell_states[cell] = new_d

        
        


class RandomPicker:
    """Randomly pick points from source. Each picked points is farthest from picked points.
    """
    def __init__(self,random_seed=65):
        self._picked = []

        try: random.seed(random_seed, version=1)  # Python 3
        except TypeError: random.seed(random_seed)  # Python 2
    
    def add_picked(self,picked):
        if not picked: raise Exception("input picked is empty")
        if isinstance(picked,Iterable):
            self._picked.extend(picked)
        else:
            self._picked.append(picked)

    @property
    def picked(self):
        return self._picked

    def picksome(self,points,picking_count,obstacles=[]):
        if picking_count==0: return
        if picking_count>len(points): raise Exception("count is larger than count of points")

        weight = [float("inf")] * len(points)
        obst_list = self._picked + obstacles
        if len(obst_list)==0:
            # self.random_pick_and_remove(points,weight)
            pass
        else:
            for p in obst_list:
                self._update_weight(points,weight,p)
        
        for _ in range(picking_count):
            self._farthest_pick_and_remove(points,weight)

    def pick(self,points):
        if len(points)==0: raise Exception("No point inputted")

        weight = [float("inf")] * len(points)
        if len(self._picked)==0:
            # self.random_pick_and_remove(points,weight)
            pass
        else:
            for p in self._picked:
                self._update_weight(points,weight,p)
        
        self._farthest_pick_and_remove(points,weight)

    def _random_pick_and_remove(self,ls,weight):
        i = random.choice(range(len(ls)))
        self._pick_and_remove(ls,weight,i)

    def _farthest_pick_and_remove(self,ls,weight):
        i = weight.index(max(weight))
        self._pick_and_remove(ls,weight,i)

    def _pick_and_remove(self,ls,weight,i):
        current_count = len(ls)
        picked_point = ls[i]

        self._picked.append(picked_point)
        del ls[i]
        del weight[i]
        current_count -= 1

        self._update_weight(ls,weight,picked_point)

    def _update_weight(self,ls,weight,point):
        assert len(ls)==len(weight)
        weights_raw = [p.DistanceTo(point) for p in ls]
        for i in range(len(ls)):
            if weights_raw[i]<weight[i]:
                weight[i] = weights_raw[i]

