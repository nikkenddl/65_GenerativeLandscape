from Rhino import Geometry as rg
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino as R
from pickle import loads
import base64

import System
import Net.SourceForge.Koogra as Excel
import System
import Clipper2Lib


class PolylineBoolenCalculation:
    ClipperPoint = Clipper2Lib.PointD
    ClipperPath = Clipper2Lib.PathD
    ClipperPathTree = Clipper2Lib.PathsD

    @classmethod
    def make_clipper_path_from_rhino_polyline(cls,rhino_polyline):
        return cls.ClipperPath([cls.ClipperPoint(p.X,p.Y) for p in rhino_polyline.GetEnumerator()])

    @classmethod
    def make_rhino_polyline_from_clipper_path(cls,pathD):
        points = [rg.Point3d(p.x,p.y,0) for p in pathD]
        points.append(points[0])
        return rg.Polyline(points)
    
    @classmethod
    def make_clipper_path_from_coordinates(cls,coordinates):
        """instance Clipper2Lib.PathD with 2d coordinates list.

        Parameters
        ----------
        coordinates : (n,2) float
            [p1(x1,y1),p2(x2,y2)...]
            first and end points must be not duplicated.

        Returns
        -------
        ClipperPathD
        """
        return cls.ClipperPath([cls.ClipperPoint(coords[0],coords[1]) for coords in coordinates])

    @classmethod
    def get_coordinates_from_clipper_path(cls,pathD):
        """get coordinates from pathD

        Parameters
        ----------
        pathD : Clipper2Lib.PathD

        Returns
        -------
        coordinates : (n,2) float
            [p1(x1,y1),p2(x2,y2)...]
            first and end points must be not duplicated.
        """
        points = [(p.x,p.y) for p in pathD]
        return points
    
    @classmethod
    def execute(cls,clip_type,fill_rule,polyline_target,polyline_operators,use_rhino=False,return_clipper_path=False):
        clipper_path_func = None # func
        restoring_result_func = None # func
        if use_rhino:
            clipper_path_func = cls.make_clipper_path_from_rhino_polyline
            restoring_result_func = cls.make_rhino_polyline_from_clipper_path
        else:
            clipper_path_func = cls.make_clipper_path_from_coordinates
            restoring_result_func = cls.get_coordinates_from_clipper_path

        path1 = clipper_path_func(polyline_target)
        paths_op = [clipper_path_func(pl) for pl in polyline_operators]
        result = cls.ClipperPathTree()

        solver = Clipper2Lib.ClipperD(2)
        solver.AddSubject(path1)
        for pl in paths_op:
            solver.AddClip(pl)

        solver.Execute(clip_type,fill_rule,result)

        if return_clipper_path:
            return result
        else:
            return [restoring_result_func(r) for r in result]

    @classmethod
    def intersect_polyline(cls,pl1,pl2,use_rhino=False,return_clipper_path=False):
        if not (pl1 and pl2):
            raise Exception("pl1 or pl2 is None")
        clip_type = Clipper2Lib.ClipType.Intersection
        nonzero_fill_rule = Clipper2Lib.FillRule.NonZero
        return cls.execute(clip_type,nonzero_fill_rule,pl1,[pl2],use_rhino=use_rhino,return_clipper_path=return_clipper_path)
    
    @classmethod
    def intersect_polylines(cls,pl1,polylines,use_rhino=False,return_clipper_path=False):
        if not (pl1 and polylines):
            raise Exception("pl1 or polylines is None")
        clip_type = Clipper2Lib.ClipType.Intersection
        nonzero_fill_rule = Clipper2Lib.FillRule.NonZero
        return cls.execute(clip_type,nonzero_fill_rule,pl1,polylines,use_rhino=use_rhino,return_clipper_path=return_clipper_path)
    
    @classmethod
    def union_polylines(cls,polylines,use_rhino=False,return_clipper_path=False):
        if len(polylines)==0:
            raise Exception("polylines is not existing")
        elif len(polylines)==1:
            if return_clipper_path:
                if use_rhino:
                    return cls.make_clipper_path_from_rhino_polyline(polylines[0])
                else:
                    return cls.make_clipper_path_from_coordinates(polylines[0])
            else:
                return polylines
            
        base = polylines[0]
        ops = polylines[1:]

        clip_type = Clipper2Lib.ClipType.Union
        nonzero_fill_rule = Clipper2Lib.FillRule.NonZero
        return cls.execute(clip_type,nonzero_fill_rule,base, ops ,use_rhino=use_rhino,return_clipper_path=return_clipper_path)
    

    @staticmethod
    def get_area_of_clipper_path(clipper_path):
        return Clipper2Lib.Clipper.Area(clipper_path)



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

class PointableRTree:
    def __init__(self,pointable_objects=[]):
        self.objects = pointable_objects
        self.rtree = rg.RTree.CreateFromPointArray([c.point for c in pointable_objects])

    def __callback_set(self,sender,e):
        e.Tag.add(e.Id)

    def __callback_list(self,sender,e):
        e.Tag.append(e.Id)

    def append(self,pointable_object):
        self.objects.append(pointable_object)
        self.rtree.Insert(pointable_object.point,self.rtree.Count)

    def extend(self,pointable_objects):
        self.objects.extend(pointable_objects)
        for o in pointable_objects:
            self.rtree.Insert(o,self.rtree.Count)
        
    
    def search_close_objects(self,origin_pointable,distance):
        close_indices = []
        sphere = rg.Sphere(origin_pointable.point,distance)
        self.rtree.Search(sphere,self.__callback_list,close_indices)
        close_objects = [self.objects[i] for i in close_indices]

        return close_objects

        

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

def get_user_texts(guid,key,raise_if_error=True):
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
        if raise_if_error: raise ValueError("key is not found : key:{}".format(key))
        else: return None   
        
    return str(rst)



def load_base64_pickle(pickledata_base64):
    return loads(base64.b64decode(pickledata_base64))



class ExcelReader:
    @staticmethod
    def read_from_file(path,sheet_index=0):
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