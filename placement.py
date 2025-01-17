import random
from collections import Iterable
from .rhinopy import CellRTree

from time import time

class ForestCreator:
    def __init__(self,
                 cell_altanatives,
                 tree_altanatives,
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

        s = time()
        self.rtree = CellRTree(cell_altanatives)
        print('time to init rtree: {}'.format(time()-s))



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
        
    def create(self):
        __time_to_pick_cell = []
        __time_to_try_to_place = []
        __time_to_update_state = []
        # for _ in range(10):
        while not self.is_created:
            # if self.is_created: break
            s = time()
            testing_cell = self.pick_cell()
            __time_to_pick_cell.append(time()-s)
            assert testing_cell is not None

            s = time()
            placed_tree = self.try_to_place(testing_cell)
            __time_to_try_to_place.append(time()-s)
            if placed_tree:
                self.__failured_count = 0
                s = time()
                self.update_state(placed_tree)
                __time_to_update_state.append(time()-s)
            else:
                self.__failured_count += 1
                testing_cell.kill()
                del self.cell_states[testing_cell]

        def print_summary(elapsed_time_list,title):
            print("\nelapsed time[s] for {}\n--------".format(title))
            total = sum(elapsed_time_list)
            cnt = len(elapsed_time_list)
            average = 0 if cnt==0 else total/cnt
            first = None if cnt==0 else elapsed_time_list[0]
            last = None if cnt==0 else elapsed_time_list[-1]
            print("total : {}".format(total))
            print("average : {}".format(average))
            print("count : {}".format(cnt))
            print("first : {}".format(first))
            print("last : {}".format(last))
            print('\n')
        print_summary(__time_to_pick_cell,'TIME_TO_PICK_CELL')
        print_summary(__time_to_try_to_place,'TIME_TO_TRY_TO_PLACE')
        print_summary(__time_to_update_state,'TIME_TO_UPDATE_STATE')
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
        filtered_trees = self.filtering(cell)
        possibility = self.possibility(filtered_trees,cell)
        placed_tree = self.placement(filtered_trees,possibility,cell)
        return placed_tree
            
    def filtering(self,cell):
        """Filtering trees by cell situation.

        Parameters
        ----------
        cell : Cell

        Returns
        -------
        filtered_trees: (n,) Tree
        """

        return [t for t in self.trees if t.matches_cell_environment(cell)]
    
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
            return None
        # tree = random.choices(tree_altanatives,weight)[0]
        # tree = random.choice(tree_altanatives)
        tree = weighted_choice(tree_altanatives,weight,1)[0]

        # add collision check here

        placed_tree = tree.place(cell)
        self.__placed_trees.append(placed_tree)
        return placed_tree
    
    def update_state(self,placed_tree):
        if any(cell.is_dead for cell in self.cell_states.keys()):
            # if some cells can't be used.
            #   - ForestRegion of cell is fullfilled
            self.cell_states = {cell:dist for cell,dist in self.cell_states.items()
                                    if not cell.is_dead}

        placed_point = placed_tree.point
        radius = placed_tree.radius
        assert placed_point is not None

        # update only closer cells
        close_cells_set = self.rtree.search_close_cells(placed_tree.placed_cell,
                                                        self.__CELL_FINDING_LIMIT_DISTANCE)

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

        try: random.seed(42, version=1)  # Python 3
        except TypeError: random.seed(42)  # Python 2
    
    def add_picked(self,picked):
        if not picked: raise Exception("input picked is empty")
        if isinstance(picked,Iterable):
            self._picked.extend(picked)
        else:
            self._picked.append(picked)

    @property
    def picked(self):
        return self._picked

    def picksome(self,points,picking_count):
        if picking_count==0: return
        if picking_count>len(points): raise Exception("count is larger than count of points")

        weight = [float("inf")] * len(points)
        if len(self._picked)==0:
            # self.random_pick_and_remove(points,weight)
            pass
        else:
            for p in self._picked:
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

