
from osgeo import ogr, gdal, osr
import logging,pprint,os

class Model_Geo:
    logging.basicConfig(
        level=logging.WARNING,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    pp = pprint.PrettyPrinter(indent=4)
    gdal.UseExceptions()
    
    not_found_geodata = 'not_found.geojson'
    
    def make_search_rect(self,pointgeom):
        
        delta = 0.00002
        minx = pointgeom.GetX()-delta
        miny = pointgeom.GetY()-delta
        maxx = pointgeom.GetX()+delta
        maxy = pointgeom.GetY()+delta
       
        return minx, miny, maxx, maxy
    
    def extract_wktlinestring_to_points(self, wkt):
        # Create a geometry object from the WKT string
        geom = ogr.CreateGeometryFromWkt(wkt)
        # Check if the geometry is a linestring
        if geom.GetGeometryType() == ogr.wkbLineString:
            # Get the number of points in the linestring
            n = geom.GetPointCount()
            # Initialize an empty list to store the coordinates
            coords = []
            # Loop through the points and append the coordinates to the list
            for i in range(n):
                x, y, z = geom.GetPoint(i)
                coords.append((y, x))
            # Return the list of coordinate pairs
            return coords
        else:
            # Return None if the geometry is not a linestring
            return None
    
    def identify_deodata(self,lat,lon,filepath,fieldname='',layer=None)->str:
        srcds = gdal.OpenEx(filepath,gdal.OF_READONLY)
        if layer is None:
            srclayer = srcds.GetLayer()
        else:
            srclayer = srcds.GetLayerByName(layer)
        
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
        
    def save_not_found_geom(self,lat,lon,filepath):
        
        if not os.path.isfile(self.not_found_geodata): 
            driver = ogr.GetDriverByName("GeoJSON")
            ds = driver.CreateDataSource(self.not_found_geodata)
            layer = ds.CreateLayer("not_found", geom_type=ogr.wkbPoint)
            layerDefn = layer.GetLayerDefn()
            filenameField = ogr.FieldDefn("filename", ogr.OFTString)
            layer.CreateField(filenameField)
        else:
            driver = ogr.GetDriverByName("GeoJSON")

            ds = driver.Open(self.not_found_geodata, 1) # 0 means read-only. 1 means writeable.
            #ds = gdal.Open(self.not_found_geodata,gdal.OF_UPDATE)
            layer = ds.GetLayer()
        
        featureDefn = layer.GetLayerDefn()
        feature = ogr.Feature(featureDefn)
        point = ogr.Geometry(ogr.wkbPoint)
        point.AddPoint(lon, lat)
        feature.SetGeometry(point)
        feature.SetField("filename", filepath)
        layer.CreateFeature(feature)
        feature = None
        
        layer=None
        ds = None
