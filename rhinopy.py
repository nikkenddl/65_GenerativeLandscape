from Rhino import Geometry as rg
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino as R
from pickle import loads
import base64

import System
import clr
# Place dll at the folder of grasshopper library
# such as D:\Users\{username}\AppData\Roaming\Grasshopper\Libraries
clr.AddReference("Net.SourceForge.Koogra")
import Net.SourceForge.Koogra as Excel


def project_to_xyplane(geometry):
    tranx = rg.Transform.PlanarProjection(rg.Plane.WorldXY)
    dup = geometry.Duplicate()
    dup.Transform(tranx)
    return dup

def compute_area(geometry):
    return rg.AreaMassProperties.Compute(geometry).Area

def try_get_point_from_string(string):
    succeeds,point =  rg.Point3d.TryParse(string)
    if not succeeds: raise Exception("failured to parse point. input:{}".format(string))
    return point

class CellRTree:
    def __init__(self,cells):
        self.cells = cells
        self.rtree = rg.RTree.CreateFromPointArray([c.point for c in cells])
        
        self.collided = set()

    def __callback_set(self,sender,e):
        e.Tag.add(e.Id)

    def __callback_list(self,sender,e):
        e.Tag.append(e.Id)
        
    
    def search_close_cells(self,origin_cell,distance):
        close_indices = []
        sphere = rg.Sphere(origin_cell.point,distance)
        self.rtree.Search(sphere,self.__callback_list,close_indices)
        close_cells = set(self.cells[i] for i in close_indices)

        return close_cells
        
        
    # def calc_each(self):
    #     def prlprocess(tp):
    #         sphere = rg.Sphere(tp[0],tp[1])
    #         self.rtree.Search(sphere,self.__callback_set,tp[2])
        
    #     collided_set_list = [set() for _ in range(len(self.r))]
        
    #     args = list(zip(self.source,self.r,collided_set_list))
        
    #     ForEach(args,prlprocess)
        
    #     #for pt,r,collided_set in zip(self.source,self.r,collided_set_list):
    #         #sphere = rg.Sphere(pt,r)
    #         #self.rtree.Search(sphere,self.__callback_set,collided_set)


    #     rst_tree = DataTree[System.Object]()
    #     for i,d in enumerate(collided_set_list):
    #         rst_tree.AddRange(list(d),ghpath(i))
    #     return rst_tree



def get_layer_objects(ghdoc,layer):
    """_summary_

    Parameters
    ----------
    layer : str

    Returns
    -------
    objs: (n,) rhino_object
    guids: (n,) str
    """
    if not isinstance(layer, str): raise Exception("method: get should receive str. received : {}".format(layer))
    
    sc.doc = R.RhinoDoc.ActiveDoc

    exists = rs.IsLayer(layer)
    if not exists: raise Exception("Layer:{} doesn't exist".format(layer))

    objs = list(rs.ObjectsByLayer(layer))
    guids = [str(obj) for obj in objs]
    sc.doc = ghdoc

    return objs,guids

def get_user_texts(guid,key):
    """get user text from guid and key

    Parameters
    ----------
    guid : str
    key :str

    Returns
    -------
    user_text: str
    """
    sc.doc = R.RhinoDoc.ActiveDoc
    try:
        rst = rs.GetUserText(guid,key=key)
    except ValueError:
        raise Exception("key is not found : key:{}".format(key))
        
    return str(rst)



def load_base64_pickle(pickledata_base64):
    return loads(base64.b64decode(pickledata_base64))



class ExcelReader:
    @staticmethod
    def read_from_file(path,sheet_index=0):
        print('path',path)
        fileExt = System.IO.Path.GetExtension(path)

        data = None
        sheets = []
        
        if fileExt.Equals(".xlsx", System.StringComparison.OrdinalIgnoreCase):
            data,sheets = ExcelReader.xlsx(path,sheet_index)
        if fileExt.Equals(".xls", System.StringComparison.OrdinalIgnoreCase):
            data,sheets = ExcelReader.xls(path,sheet_index)

        if not data:
            raise Exception("loaded no data")
        return data,sheets
    
    @staticmethod
    def xlsx(f,id):
        stream = System.IO.FileStream(f,
                                      System.IO.FileMode.Open,
                                      System.IO.FileAccess.Read,
                                      System.IO.FileShare.ReadWrite)
        wb = Excel.Excel2007.Workbook(stream)
        stream.Dispose()
        sheets = [ws.Name for ws in wb.GetWorksheets()]
        if id==None:
            return None,sheets
        ws = wb.GetWorksheet(id)
        rows = ws.LastRow+1
        cols = ws.LastCol+1
        mat = []
        for i in range(rows):
            row = ws.GetRow(i)
            values = [row.GetCell(j).Value for j in range(cols)]
            mat.append(ExcelReader.null_to_emptytext(values))

        return mat,sheets

    @staticmethod
    def xls(f,id):
        raise NotImplementedError()
        # data = []
        # stream = System.IO.FileStream(f,
        #                               System.IO.FileMode.Open,
        #                               System.IO.FileAccess.Read,
        #                               System.IO.FileShare.ReadWrite)
        # wb = Excel.Excel.Workbook(stream)
        # stream.Dispose()
        # sheets = [ws.Name for ws in wb.Worksheets]
        # if id==None:
        #    return None,None,None,sheets
        # for i,n in enumerate(wb.Worksheets):
        #     if i == id:
        #         rows = n.LastRow+1
        #         cols = n.LastCol+1
        #         for j in range(rows):
        #             row = n.Rows.GetRow(j)
        #             for k in range(cols):
        #                 if row != None and row.GetCell(k) != None:
        #                     d = row.GetCell(k).Value
        #                     data.append(d)
        # return data, sheets

    @staticmethod
    def null_to_emptytext(ls):
        return ["" if d is None else d for d in ls]