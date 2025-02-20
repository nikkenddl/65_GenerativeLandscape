class MapEvaluator:
    def __init__(self,cells):
        self.cells = cells

    def evaluate_best_forest_domain(self,forest_domains,trees):
        def find_trees_by_speacies(species_list):
            rst = []
            for species in species_list:
                rst.extend(t for t in trees if t.species==species)
            return rst
        
        forest_domains = sorted(forest_domains,key=lambda fd: fd.name)
        forest_domain_names = [fd.name for fd in forest_domains]
        each_dominant_species = [fd.dominant_species for fd in forest_domains]
        each_dominant_trees = [find_trees_by_speacies(species_list) for species_list in each_dominant_species]
        

        #rst = [{fd1.name:placable_ratio, fd2.name:placable_ratio,}...]
        count_forest_domain = len(forest_domain_names)
        result = [[0.0]*count_forest_domain for _ in range(len(self.cells))]
        for c,rstls in zip(self.cells,result):
            for i_dom,(trees,species) in enumerate(zip(each_dominant_trees,each_dominant_species)):
                species_count = len(species)
                # print(tree_count)
                if species_count==0: continue # no dominant trees in the domain

                placable_trees = [t for t in trees if t.matches_cell_environment(c)[0]]
                placable_speacies_count = len(set(t.species for t in placable_trees))
                # print(placable_count)
                # print("----")
                rstls[i_dom] = float(placable_speacies_count)/float(species_count)
        
        # best_domain = [forest_domain_names[rstls.index(max(rstls))] for rstls in result]
        cell_values = list(map(list, zip(*result)))

        return forest_domain_names,cell_values
    




