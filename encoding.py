#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Archive arrangement data of Trees on Cells into a JSON file.
Reconstruction is possible from the archived JSON.
Note:
- In the JSON, each cell is stored without an embedded tree.
- Each tree (if placed) only contains a reference to its cell via placed_cell_id.
"""

import json

def point_to_dict(point):
    """
    Convert a point object into a dictionary.
    Assumes point has attributes: X, Y, Z.
    Adjust if your point class differs.
    """
    if point is None:
        return None
    return {"X": point.X, "Y": point.Y, "Z": point.Z}

def cell_to_dict(cell):
    """
    Convert a Cell object into a serializable dictionary.
    All information required for reconstruction is serialized.
    Note: The placed_tree reference is not saved.
    """
    cell_dict = {
        "ID": cell.ID,
        "point": point_to_dict(cell.point),
        # Save only the forest_region's id (assuming forest_region has an ID attribute)
        "forest_region_id": cell.forest_region.ID if cell.forest_region is not None else None,
        "soil_thickness": cell.soil_thickness,
        "wind_speed": cell.wind_speed,
        "sunshine_duration": cell.sunshine_duration,
        "distance_to_edge": cell.distance_to_edge,
        "status": cell.status,
        # Access the private is_killed flag via name mangling.
        "is_killed": cell._Cell__is_killed,
        # Save the computed tree height limit.
        "tree_height_limit": cell.tree_height_limit
    }
    return cell_dict

def tree_to_dict(tree):
    """
    Convert a Tree object into a serializable dictionary.
    All information required for reconstruction is serialized.
    If the tree has been placed, only the placed_cell's ID is stored.
    """
    # Get the placed point of tree; use the private attribute.
    placed_point = tree._Tree__placed_point
    tree_dict = {
        "species": tree.species,
        "symbol": tree.symbol,
        # Accessing the private stored height (in mm) via name mangling.
        "height": tree._Tree__height,
        "trunk_circumference": tree.trunk_circumference,
        "DH_ratio": tree.DH_ratio,
        "maximum_height": tree.maximum_height,
        "undercut_height_ratio": tree.undercut_height_ratio,
        "root_radius": tree._Tree__root_radius,
        "safety_distance": tree.safety_distance,
        "age": tree._Tree__age,
        "initial_age": tree._Tree__initial_age,
        "initial_height": tree._Tree__initial_height,
        "age_estimation_cache": tree._Tree__age_estimation_cache,
        "height_estimation_cache": tree._Tree__height_estimation_cache,
        "tree_shape_cache": tree._Tree__tree_shape_cache,
        "shade_tolerance_index": tree._Tree__shade_tolerance_index,
        "wind_tolerance_index": tree._Tree__wind_tolerance_index,
        # Reference to the placed cell via its ID, if any.
        "placed_cell_id": tree.placed_cell.ID if tree.placed_cell is not None else None,
        "placed_point": point_to_dict(placed_point),
        "is_damy": tree.is_damy,
        "growing_speed": tree.growing_speed,
        "growing_parameter_k": tree.growing_parameter_k,
        "growing_parameter_B": tree.growing_parameter_B,
        "root_type": tree.root_type,
        # Serialize custom_tags as a list rather than a set.
        "custom_tags": list(tree.custom_tags)
    }
    return tree_dict

def archive_to_json(cells, trees, filepath):
    """
    Assemble the data from cells and trees and write to a JSON file.
    The JSON contains two keys: "cells" and "trees".
    """
    data = {
        "cells": [cell_to_dict(cell) for cell in cells],
        "trees": [tree_to_dict(tree) for tree in trees]
    }
    
    with open(filepath, "w") as f:
        # indent=2 for readability
        json.dump(data, f, indent=2)




# Example usage (assuming you have lists of Cell instances "cells" and Tree instances "trees"):
if __name__ == "__main__":
    # Here you would normally obtain or create your cells and trees.
    # For the sake of example, suppose:
    cells = []  # List of Cell objects
    trees = []  # List of Tree objects

    # ... your code that populates 'cells' and 'trees' ...

    output_file = "arrangement_archive.json"
    archive_to_json(cells, trees, output_file)
    print("Archive has been saved to: {}".format(output_file))