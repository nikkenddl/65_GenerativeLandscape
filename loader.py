import os

def get_source_reload():
    ghpy_path = os.path.join(__file__,os.path.pardir,'.reload_library.ghpy')

    code = ""
    with open(ghpy_path) as f:
        code= f.read()
    return code

def get_source_load_const():
    output_names = ['map_layer_name',
                    'map_keys',
                    'forest_region_layer',
                    'forest_region_archive_layer',
                    'forest_region_keys',
                    'preplaced_tag']
    ghpy_path = os.path.join(__file__,os.path.pardir,'.load_const.ghpy')

    code = ""
    with open(ghpy_path) as f:
        code= f.read()

    return output_names,code

def get_source_load_tree_asset():
    output_names = ['tree_asset']
    ghpy_path = os.path.join(__file__,os.path.pardir,'.load_tree_asset.ghpy')

    code = ""
    with open(ghpy_path) as f:
        code= f.read()

    return output_names,code

def get_source_load_forest_domain():
    output_names = ['layer_name','forest_domain']
    ghpy_path = os.path.join(__file__,os.path.pardir,'.load_forest_domain.ghpy')

    code = ""
    with open(ghpy_path) as f:
        code= f.read()

    return output_names,code

def get_source_load_forest_region():
    output_names = ['forest_region']
    ghpy_path = os.path.join(__file__,os.path.pardir,'.load_forest_region.ghpy')

    code = ""
    with open(ghpy_path) as f:
        code= f.read()

    return output_names,code

def get_source_load_map():
    output_names = [
        'grid',
        'x_cell_count',
        'y_cell_count',
        'grid_origin',
        'span',
        'cells',
        'invalid_cell_points',
        'created_time']
    ghpy_path = os.path.join(__file__,os.path.pardir,'.load_map.ghpy')

    code = ""
    with open(ghpy_path) as f:
        code= f.read()

    return output_names,code
