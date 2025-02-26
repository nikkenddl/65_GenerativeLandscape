#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Reconstruct Cells and Trees from a JSON archive.

Assumptions:
- The JSON file contains two keys: "cells" and "trees".
- The Cell record stores "forest_region_id" but not the full forest_region;
  a dummy or lookup value will be used for reconstruction.
- The Tree record stores a "placed_cell_id" field that references a Cell.
- The point objects are represented as dictionaries with "X", "Y", and "Z".
- Reconstruction bypasses the __init__ methods, so any runtime registration
  (like appending a cell to a forest_region’s list) must be done separately.
"""

import json
from .Tree import Tree
from .Cell import Cell

from Rhino.Geometry import Point3d


def dict_to_point(d):
    """
    Convert a dictionary to a Point object.
    Expects a dictionary with keys "X", "Y", "Z".
    """
    if d is None:
        return None
    return Point3d(d["X"], d["Y"], d["Z"])

# A dummy forest region class for reconstruction.
class DummyForestRegion(object):
    def __init__(self, ID):
        self.ID = ID
        # You may add additional default attributes here if needed.
        self.cells = []  # For compatibility with Cell.__init__

    def __repr__(self):
        return "DummyForestRegion(ID=%s)" % self.ID

# Reconstruction function for a Cell.
def reconstruct_cell(cell_dict, forest_regions=None):
    """
    Reconstruct a Cell instance from its dictionary representation.

    Parameters:
      cell_dict: The dictionary representing the Cell.
      forest_regions: (optional) A dict mapping forest_region_id to a forest region object.
                      If not provided, a DummyForestRegion is created.
                      
    Returns:
      A Cell object with all attributes restored.
    """
    # Create the instance without calling __init__
    cell = Cell.__new__(Cell)
    
    # Set public attributes.
    cell.ID = cell_dict["ID"]
    cell.point = dict_to_point(cell_dict["point"])
    # For forest_region, use the provided one or create a dummy.
    fr_id = cell_dict.get("forest_region_id")
    if forest_regions and fr_id in forest_regions:
        cell.forest_region = forest_regions[fr_id]
    else:
        cell.forest_region = DummyForestRegion(fr_id)
    cell.soil_thickness = cell_dict["soil_thickness"]
    cell.wind_speed = cell_dict["wind_speed"]
    cell.sunshine_duration = cell_dict["sunshine_duration"]
    cell.distance_to_edge = cell_dict["distance_to_edge"]
    cell.status = cell_dict.get("status", "")
    
    # Set private attributes (using name mangling).
    cell.tree_height_limit = cell_dict.get("tree_height_limit")
    
    # If the cell originally appended itself to forest_region.cells,
    # you might want to do that here.
    if cell.forest_region:
        cell.forest_region.cells.append(cell)
    
    return cell

# Reconstruction function for a Tree.
def reconstruct_tree(tree_dict, cells_by_id):
    """
    Reconstruct a Tree instance from its dictionary representation.

    Parameters:
      tree_dict: The dictionary representing the Tree.
      cells_by_id: A dictionary mapping cell IDs to Cell objects.
      
    Returns:
      A Tree object with all attributes restored.
    """
    # Create the instance without calling __init__
    tree = object.__new__(Tree)
    
    # Set public attributes.
    tree.species = tree_dict.get("species")
    tree.symbol = tree_dict.get("symbol")
    tree.trunk_circumference = tree_dict.get("trunk_circumference")
    
    # Set private attributes (via name mangling).
    tree._Tree__height = tree_dict.get("height")
    tree.DH_ratio = tree_dict.get("DH_ratio")
    tree.maximum_height = tree_dict.get("maximum_height")
    tree.undercut_height_ratio = tree_dict.get("undercut_height_ratio")
    tree._Tree__root_radius = tree_dict.get("root_radius")
    tree.safety_distance = tree_dict.get("safety_distance")
    tree._Tree__age = tree_dict.get("age")
    tree._Tree__initial_age = tree_dict.get("initial_age")
    tree._Tree__initial_height = tree_dict.get("initial_height")
    tree._Tree__age_estimation_cache = tree_dict.get("age_estimation_cache", {})
    tree._Tree__height_estimation_cache = tree_dict.get("height_estimation_cache", {})
    tree._Tree__tree_shape_cache = tree_dict.get("tree_shape_cache", {})
    tree._Tree__shade_tolerance_index = tree_dict.get("shade_tolerance_index")
    tree._Tree__wind_tolerance_index = tree_dict.get("wind_tolerance_index")
    
    # For placed_cell, use the saved cell id to look up the cell.
    placed_cell_id = tree_dict.get("placed_cell_id")
    if placed_cell_id is not None and placed_cell_id in cells_by_id:
        tree.placed_cell = cells_by_id[placed_cell_id]
    else:
        tree.placed_cell = None

    tree._Tree__placed_point = dict_to_point(tree_dict.get("placed_point"))
    tree.is_damy = tree_dict.get("is_damy")
    tree.growing_speed = tree_dict.get("growing_speed")
    tree.growing_parameter_k = tree_dict.get("growing_parameter_k")
    tree.growing_parameter_B = tree_dict.get("growing_parameter_B")
    tree.root_type = tree_dict.get("root_type")
    
    # custom_tags was archived as a list; convert it back to a set.
    tree.custom_tags = set(tree_dict.get("custom_tags", []))
    
    return tree

def reconstruct_archive(filepath, forest_regions=None):
    """
    Reconstruct Cells and Trees from a given JSON archive file.

    Parameters:
      filepath: The path to the JSON archive.
      forest_regions: (optional) A dict mapping forest region IDs to forest
                      region objects. If not provided, DummyForestRegion objects
                      will be used when reconstructing cells.
                      
    Returns:
      A tuple (cells, trees) where:
        cells: list of reconstructed Cell objects.
        trees: list of reconstructed Tree objects.
    """
    with open(filepath, "r") as f:
        data = json.load(f)

    cells_data = data.get("cells", [])
    trees_data = data.get("trees", [])

    # Reconstruct cells.
    cells = []
    cells_by_id = {}
    for cell_dict in cells_data:
        cell = reconstruct_cell(cell_dict, forest_regions)
        cells.append(cell)
        cells_by_id[cell.ID] = cell

    # Now reconstruct trees.
    trees = []
    for tree_dict in trees_data:
        tree = reconstruct_tree(tree_dict, cells_by_id)
        trees.append(tree)

    return cells, trees

# Example usage:
if __name__ == "__main__":
    # Path to the archive JSON file created earlier.
    archive_file = "arrangement_archive.json"
    
    # Optionally, if you have a forest region registry, create a dict mapping IDs.
    # For this example, we use an empty dict so that DummyForestRegion objects are used.
    forest_regions = {}
    
    cells, trees = reconstruct_archive(archive_file, forest_regions)
    
    print("Reconstructed %d cells." % len(cells))
    print("Reconstructed %d trees." % len(trees))
    
    # Display some reconstructed objects:
    for c in cells:
        print("Cell:", c.ID, c.point, c.forest_region)
    for t in trees:
        print("Tree:", t.symbol, t.species, "placed in cell:",
              t.placed_cell.ID if t.placed_cell else None)