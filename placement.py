import random
from collections import Iterable,defaultdict
from .rhinopy import PointableRTree
from .config import Config
from . import log
from .Cell import Cell
from .Forest import ForestRegion
import math
import traceback

from time import time

class ForestCreator:
    __config = Config()
    __LOG_FILE_LOCATION =  __config.forest_creator_log_file_path
    __LOG_AUTOFLUSH_COUNT=100
    __log_archive = []
    __log_count = 0
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
        self.log('time to clear cell: {}'.format(time()-s))
        self.__flush()
        
        self.__CELL_FINDING_LIMIT_DISTANCE = 5000.0
        s = time()
        self.cell_states = {cell : self.__CELL_FINDING_LIMIT_DISTANCE for cell in cell_altanatives}
        self.log('time to init cell state: {}'.format(time()-s))
        self.__flush()

        self.trees = tree_altanatives
        
        self.__failured_count = 0
        self.__limit_failured_count = int(limit_iteration)
        self.__placed_trees = []

        self.preplaced_unplaced_trees = []

        s = time()
        self.all_cell_rtree = PointableRTree(cell_altanatives)
        self.log('time to init all_cell_rtree: {}'.format(time()-s))
        self.__flush()

        self.placed_tree_rtree = PointableRTree([])

        s = time()
        self.init_preplaced(placement_postponed_trees)
        self.log('time to init preplaced trees: {}'.format(time()-s))
        self.__flush()
        


    def clear_cells(self,cells):
        s = time()
        for c in cells:
            c.clear()
        self.log('time to clear cell : {}'.format(time()-s))
        s = time()
        frs = set(c.forest_region for c in cells)
        self.log('time to create set of forest regions : {}'.format(time()-s))
        s = time()
        for fr in frs:
            fr.initialize()
        self.log('time to init forest regions: {}'.format(time()-s))
        self.log('count of forest region: {}'.format(len(frs)))


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

    @classmethod
    def log(cls,msg,*args):
        msg = str(msg)
        if args:
            msg += " | "
            msg += " | ".join(str(a) for a in args)

        cls.__log_archive.append(msg)

        cls.__log_count += 1
        if cls.__LOG_AUTOFLUSH_COUNT<cls.__log_count:
            cls.__flush()

    @classmethod
    def __flush(cls):
        cls.__log_count = 0
        if cls.__log_archive:
            path = log.create_incremented_file(cls.__LOG_FILE_LOCATION,1028*1028*50)
            log.write(path,"\n".join(cls.__log_archive))

        cls.__log_archive = []
            
        
    def create(self):
        ## initial height 
        trees_high = [t for t in self.trees if t.initial_height>=self.__config.high_tree_shortest_height_class]
        minimum_required_soil_thickness_for_high_trees = self.__config.required_soil_thickness_by_height_category[self.__config.high_tree_shortest_height_class]
        cells_for_high_trees = [c for c in self.cell_states.keys() if c.soil_thickness>=minimum_required_soil_thickness_for_high_trees]
        cells_for_high_trees_set = set(cells_for_high_trees)

        __placed_count = 0
        try:
            __time_to_pick_cell = []
            __time_to_try_to_place = []
            __time_to_update_state = []
            __failured_status = []
            # for _ in range(10):
            while True:
                if self.is_created:
                    self.log("INFO: Finished Creation")
                    try:
                        for fr in ForestRegion._regions:
                            self.log("INFO: region<{}> created status-{}".format(fr.ID,fr.has_finished_placement))
                            self.log("DEBUG: region tree count (placed[all]/target): {}/{}".format(len(fr.placed_trees),fr.limit_tree_count))
                    except:
                        self.log("ERROR:failed to log")
                    break

                s = time()
                testing_cell = self.pick_cell(cells_for_high_trees)
                __time_to_pick_cell.append(time()-s)
                
                if testing_cell is None:
                    self.log("Finish palcing process because testing cell is None.")
                    break


                s = time()
                assert isinstance(testing_cell,Cell)
                # if the testing cell is in a no-gap region, try to place some trees closely together.
                is_cell_in_nogap_region = math.isinf(testing_cell.FD_gap_size)
                loop_limit = self.__config.trying_placement_count_in_nogap_region if is_cell_in_nogap_region else 1
                close_cells = None
                if is_cell_in_nogap_region:
                    close_cells = self.all_cell_rtree.search_close_objects(testing_cell,self.__config.trying_multiplacement_radius_in_nogap_region)
                    # remove dead cells
                    close_cells = [c for c in close_cells if c in self.cell_states and c in cells_for_high_trees_set]
                    if len(close_cells)<=1: # if close_cells is empty or contains only testingcell
                        self.log("INFO: NO CLOSE CELL of testing cell:{}".format(testing_cell.ID))
                        loop_limit = 1
                    else:
                        random.shuffle(close_cells)

                for i_dense_placement in range(loop_limit):
                    self.log("DEBUG:Trying cell:{} / FRID:{} / FDname:{}".format(testing_cell,testing_cell.forest_region.ID,testing_cell.FDname))
                    placed_tree,status = self.try_to_place(testing_cell,trees_high)
                    __time_to_try_to_place.append(time()-s)
                    if placed_tree:
                        __placed_count += 1
                        self.log("INFO: {}/{} is placed : placed total {}".format(placed_tree.species,placed_tree.symbol,__placed_count))
                        self.__failured_count = 0
                        s = time()
                        self.update_state(placed_tree)
                        __time_to_update_state.append(time()-s)

                        
                    else:
                        self.log("DEBUG: failed and removed / {}".format(status))
                        # It is impossible to place the tree in the cell.
                        __failured_status.append(status)
                        self.__failured_count += 1
                        testing_cell.kill(status)
                        try: del self.cell_states[testing_cell]
                        except: self.log("ERROR: failed to del from self.cell_states")


                    if i_dense_placement==loop_limit-1:
                        # last inner loop
                        break
                    elif len(close_cells)<=1: # type: ignore if close_cells is empty or contains only testingcell
                        self.log("INFO: All close cells are remove")
                        break
                    else:
                        # update testing cell
                        self.log("DEBUG: try to place close to testing cell. : try_count-{}".format(i_dense_placement))
                        close_cells = [c for c in close_cells if c!=testing_cell and c in self.cell_states] # type:ignore - remove placed testing cell from close_cells
                        # testing_cell = self.pick_cell(close_cells)
                        # if not testing_cell:
                        #     break

                        if not close_cells: break
                        testing_cell = close_cells[0]



            def log_summary(elapsed_time_list,title):
                self.log("\nelapsed time[s] for {}\n--------".format(title))
                total = sum(elapsed_time_list)
                cnt = len(elapsed_time_list)
                average = 0 if cnt==0 else total/cnt
                self.log("total : {}".format(total))
                self.log("average : {}".format(average))
                self.log("count : {}".format(cnt))
                self.log('\n')

            log_summary(__time_to_pick_cell,'TIME_TO_PICK_CELL')
            log_summary(__time_to_try_to_place,'TIME_TO_TRY_TO_PLACE')
            log_summary(__time_to_update_state,'TIME_TO_UPDATE_STATE')
            self.__flush()
            return self.__placed_trees
        except Exception as e:
            self.log('failed in ForestCreater.create()')
            self.log(traceback.format_exc())
            self.__flush()
            raise Exception(e)


    def post_create(self,trying_cells):
        """place only short trees

        Parameters
        ----------
        trying_cells : _type_
            _description_

        Returns
        -------
        _type_
            _description_
        """
        self.log('Executing post_create------------------------------')
        trees_short = [t for t in self.trees if t.height_category<self.__config.high_tree_shortest_height_class]
        if not trees_short:
            self.log("WARN: no short trees")
            return []
        
        placed_trees = []
        for testing_cell in trying_cells:
            assert testing_cell is not None

            placed_tree,status = self.try_to_place(testing_cell,trees_short,places_damy=True)
            if not placed_tree:
                self.log("failured to place: {}".format(status))
            placed_trees.append(placed_tree)
        self.__flush()
        return placed_trees


    @property
    def is_created(self):
        # too many failured.
        if self.__failured_count>=self.__limit_failured_count:
            self.log("Over failured limit: {}".format(self.__failured_count))
            return True
        # tree counts is enough for all region => all cells are removed.
        if len(self.cell_states)==0:
            self.log("finish because density goal is reached.")
            return True

        # default
        return False
    
    def pick_cell(self,cells=None):
        cells = cells or self.cell_states.keys()
        farthest_dist = -float('inf')
        farthest_cell = None
        for cell in cells:
            if cell not in self.cell_states: continue
            dist = self.cell_states[cell]
            if dist>=self.__CELL_FINDING_LIMIT_DISTANCE:
                farthest_cell = cell
                break
            if dist>farthest_dist:
                farthest_cell = cell
                farthest_dist = dist
        return farthest_cell

    
    def try_to_place(self,cell,trees,places_damy=False):
        filtered_trees,status = self.filtering(cell,trees)
        if not filtered_trees:
            return None,status
        possibility = self.possibility(filtered_trees,cell)
        placed_tree,status = self.placement(filtered_trees,possibility,cell,places_damy=places_damy)
        return placed_tree,status
            
    def filtering(self,cell,trees):
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
        ls_is_cleared = [t.matches_cell_environment(cell,ForestCreator.log) for t in trees]

        
        if not (any(rst[0] for rst in ls_is_cleared)):
            statuses = [rst[1] for rst in ls_is_cleared]
            counter = count_defaultdict(statuses)
            message = " / ".join("{}:{}".format(key,count) for key,count in counter.items())
            # return [],most_status
            return [],"No Filtered Trees : {}".format(message)
        trees_matches_environment = [t for t,rst in zip(trees,ls_is_cleared) if rst[0]]
        
       
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
                trees_matches_environment = [t for t in trees_matches_environment if t.height_category in height_category_in_vicinity]
            if not trees_matches_environment:
                return [], "No rest things after forest layer filtering"

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
            _,goal_over_current_dominant = cell.forest_region.evaluate_dominant()
            dominant_possibility = 0.7/float(count_dominant) * (goal_over_current_dominant**4) # adjust by current eval value
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
            _,goal_over_current_egdd = cell.forest_region.evaluate_egdd()
            eg_possibility = eg_ratio/float(count_EG) * (goal_over_current_egdd**4) # adjust by current eval value
            dd_possibility = dd_ratio/float(count_DD)
            for i in range(L):
                if are_EG[i]:
                    possibility_list[i] *= eg_possibility
                else:
                    possibility_list[i] *= dd_possibility

        return possibility_list
    
    
    def placement(self,tree_altanatives,weight,cell,places_damy=False):
        """select a tree from altanatives according to the weight and place a tree.
        if places_damy, places a tree without registration of the tree and the cell.
        The parameter should be used in post_create.

        Parameters
        ----------
        tree_altanatives : _type_
            _description_
        weight : _type_
            _description_
        cell : _type_
            _description_
        places_damy : bool, optional
            _description_, by default False
        """
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

        # place damy to apply the tree height limit by soil thickness of the cell.
        tree = weighted_choice(tree_altanatives,weight,1)[0].place(cell,is_damy=True)
        overlapping_neighbors=[]

        # add collision check here
        close_placed_trees = self.placed_tree_rtree.search_close_objects(cell,self.__config.radius_to_check_collision)
        if close_placed_trees:
            # root collision
            if not all(tree.checks_root_collision(t,cell.point) for t in close_placed_trees):
                return None, "The placing tree root collides to already placed tree roots."

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
                return None,"Placing Tree<{}/r:{}/h:{}> is too close with already placed trees".format(tree.species,tree.radius,tree.height)

        # place tre trying tree
        placed_tree = tree.place(cell,is_damy=places_damy)
        placed_tree.register_overlapped_trees(overlapping_neighbors)

        # Register the placed tree as an overlapped tree with neighbours.
        for neighbor in overlapping_neighbors:
            neighbor.register_overlapped_tree(placed_tree)

        return placed_tree,"OK"
        
    
    def update_state(self,placed_tree):
        """Remove killed or placed cells from self.cell_states and update distances

        Parameters
        ----------
        placed_tree : Tree
        """
        # register the placed tree to cache
        self.__placed_trees.append(placed_tree)
        self.placed_tree_rtree.append(placed_tree)

        dead_cells = [cell for cell in self.cell_states.keys() if cell.is_dead]

        if dead_cells:
            # if some cells can't be used.
            #   - ForestRegion of cell is fullfilled
            if len(dead_cells)<=30:
                for dc in dead_cells:
                    self.log("DEBUG: cell<{}> in region<{}> is removed".format(dc.ID,dc.forest_region.ID))
                    del self.cell_states[dc]
            else:
                self.log("Many cells are removed in one time. Display only 30 cells")
                for dc in dead_cells[:30]:
                    self.log("DEBUG: cell<{}> in region<{}> is removed".format(dc.ID,dc.forest_region.ID))
                dead_set = set(dead_cells)
                self.cell_states = dict((cell,dist) for cell,dist in self.cell_states.items() if cell not in dead_set)

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

    def picksome(self,points,picking_count,picking_radius=0.0,obstacles=[]):
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
            self._farthest_pick_and_remove(points,weight,picking_radius=picking_radius)

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

    def _farthest_pick_and_remove(self,ls,weight,picking_radius=0.0):
        i = weight.index(max(weight))
        self._pick_and_remove(ls,weight,i,picking_radius=picking_radius)

    def _pick_and_remove(self,ls,weight,i,picking_radius=0.0):
        current_count = len(ls)
        picked_point = ls[i]

        self._picked.append(picked_point)
        del ls[i]
        del weight[i]
        current_count -= 1

        self._update_weight(ls,weight,picked_point,picking_radius=picking_radius)

    def _update_weight(self,ls,weight,point,picking_radius=0.0):
        assert len(ls)==len(weight)
        weights_raw = [p.DistanceTo(point)-picking_radius for p in ls]
        for i in range(len(ls)):
            if weights_raw[i]<weight[i]:
                weight[i] = weights_raw[i]

