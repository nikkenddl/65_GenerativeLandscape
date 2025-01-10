# -*- coding: utf-8 -*-
# 
from conversion import try_get_float

class ForestDomain:
    def __init__(self, name, density, overlap_tolerance_ratio, count_top_layer_species, eg_dd_ratio, eg_dd_ratio_in_gap, gap_size, dominant_species):
        self.name = str(name)
        assert density is not None

        # Convert density from trees per 100m^2 to trees per mm^2
        self.density = try_get_float(density) / (100 * 1000000)  # 1m² = 1000000mm²

        self.overlap_tolerance_ratio = try_get_float(overlap_tolerance_ratio,0.0)
        self.count_top_layer_species = int(count_top_layer_species)
        self.eg_dd_ratio = try_get_float(eg_dd_ratio,0.5)
        self.eg_dd_ratio_in_gap = try_get_float(eg_dd_ratio_in_gap,0.5)
        self.gap_size = try_get_float(gap_size,float('inf'))
        if self.gap_size: self.gap_size *= 1000000
        
        # Split dominant_species using '/' and store as a list
        self.dominant_species = dominant_species.split('/')
        
    def copy(self):
        """Creates and returns a copy of the current ForestDomain instance."""
        new_instance = ForestDomain.__new__(ForestDomain)  # Create a new instance without calling __init__
        new_instance.name = self.name
        new_instance.density = self.density
        new_instance.overlap_tolerance_ratio = self.overlap_tolerance_ratio
        new_instance.count_top_layer_species = self.count_top_layer_species
        new_instance.eg_dd_ratio = self.eg_dd_ratio
        new_instance.eg_dd_ratio_in_gap = self.eg_dd_ratio_in_gap
        new_instance.gap_size = self.gap_size
        new_instance.dominant_species = list(self.dominant_species)  # Copy the list
        return new_instance

    def __str__(self):
        return ("ForestDomain(name={}, density={:.10f}, overlap_tolerance_ratio={}, count_top_layer_species={}, "
                "eg_dd_ratio={}, eg_dd_ratio_in_gap={}, gap_size={}, dominant_species={})").format(
            self.name, self.density, self.overlap_tolerance_ratio, self.count_top_layer_species,
            self.eg_dd_ratio, self.eg_dd_ratio_in_gap, self.gap_size, self.dominant_species)