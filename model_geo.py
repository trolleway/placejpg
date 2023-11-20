
from osgeo import ogr, gdal, osr
import logging,pprint

class Model_Geo:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    pp = pprint.PrettyPrinter(indent=4)
    gdal.UseExceptions()
    
    def make_search_rect(self,pointgeom):
        
        delta = 0.0002
        minx = pointgeom.GetX()-delta
        miny = pointgeom.GetY()-delta
        maxx = pointgeom.GetX()+delta
        maxy = pointgeom.GetY()+delta
       
        return minx, miny, maxx, maxy
    
    def identify_deodata(self,lat,lon,filepath,fieldname)->str:
        srcds = gdal.OpenEx(filepath,gdal.OF_READONLY)
        srclayer = srcds.GetLayer()
        
        point_geom = ogr.Geometry(ogr.wkbPoint)
        point_geom.AddPoint(lon, lat)
        minx, miny, maxx, maxy = self.make_search_rect(point_geom)
        srclayer.ResetReading()
        srclayer.SetSpatialFilterRect(minx, miny, maxx, maxy)
        srclayer.ResetReading()
        
        if srclayer.GetFeatureCount() < 1:
            del srclayer
            del srcds
            return None
        else:
            feature = srclayer.GetNextFeature()
            try:
                val = feature.GetField(fieldname)
            except:
                return None
            del srclayer
            del srcds
            return val            
