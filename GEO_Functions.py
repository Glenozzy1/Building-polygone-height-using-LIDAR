import math
import os
from typing import List, Any
import numpy as np
import pandas as pd
from pyproj import Transformer
import rasterio
import geopandas as gpd
from shapely.geometry import Polygon, Point
import laspy
import sys
#from pyproj import CRS
#from pyproj.aoi import AreaOfInterest
#from pyproj.database import query_utm_crs_info

def distance_haversine(startpoint_longitude, startpoint_latitude, endpoint_longitude, endpoint_latitude, unit):
    """
    This uses the ‘haversine’ formula to calculate the great-circle distance between two points – that is,
    the shortest distance over the earth’s surface – giving an ‘as-the-crow-flies’ distance between the points
    (ignoring any hills they fly over, of course!).
    Haversine
    formula:    a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
    c = 2 ⋅ atan2( √a, √(1−a) )
    d = R ⋅ c
    where   φ is latitude, λ is longitude, R is earth’s radius (mean radius = 6,371km);
    note that angles need to be in radians to pass to trig functions!
    By default, the haversine function returns distance in km.

    """
    R = 6371.0088  # Radius of the Earth = 6378.1 km, mean radius = 6,371km
    startpoint_latitude, startpoint_longitude, endpoint_latitude, endpoint_longitude = map(np.radians, [startpoint_latitude, startpoint_longitude, endpoint_latitude, endpoint_longitude])
    dlat = endpoint_latitude - startpoint_latitude
    dlon = endpoint_longitude - startpoint_longitude
    a = np.sin(dlat / 2) ** 2 + np.cos(startpoint_latitude) * np.cos(endpoint_latitude) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(a ** 0.5, (1 - a) ** 0.5)
    distance = R * c  # distance KM
    if unit == "Meters":
        distance = distance * 1000
    return round(distance, 2)


def end_point_given_azm_distance(longitude, latitude, bearing, distance_in_meters):
    # Get lat/long given current point, distance and bearing
    # Distance is in KM
    # convert distance to KM
    distance = distance_in_meters / 1000  # convert distance to KM

    R = 6371  # Radius of the Earth = 6378.1 km, mean radius = 6,371km
    R_Bearing = math.radians(bearing)
    R_longitude = math.radians(longitude)  # Current long point converted to radians
    R_latitude = math.radians(latitude)  # Current lat point converted to radians
    EndPoint_Latitude_Radians = math.asin(
        math.sin(R_latitude) * math.cos(distance / R) + math.cos(R_latitude) * math.sin(distance / R) * math.cos(
            R_Bearing))
    EndPoint_Longitude_Radians = R_longitude + math.atan2(
        math.sin(R_Bearing) * math.sin(distance / R) * math.cos(R_latitude),
        math.cos(distance / R) - math.sin(R_latitude) * math.sin(EndPoint_Latitude_Radians))
    # convert back to degrees
    EndPoint_Latitude = math.degrees(EndPoint_Latitude_Radians)
    EndPoint_Longitude = math.degrees(EndPoint_Longitude_Radians)
    return EndPoint_Longitude, EndPoint_Latitude


def epsg_transform_point(value_1, value_2, input_epsg, output_epsg):
    # input data frame deg, start point, end point in lat long format
    #  Coord_EPSG = 'epsg:4326'  #  Open Streets, Google Earth wgs84 datum. (EPSG: 4326) order Lat, long surface of a sphere or ellipsoid of reference
    #  Coord_EPSG = 'epsg:3857'  #  Open Streets Tile server, Google Maps wgs84 datum. (EPSG 3857) order long, lat coordinate system PROJECTED from the surface of the sphere or ellipsoid to a flat surface.
    #  Coord_EPSG = 'epsg:6346'  #  NAD83(2011) datum / UTM zone 17N  order long, lat
    #  Coord_EPSG = 'epsg:6349'  #  NAD83(2011) datum  all of USA order lat, long
    #  Coord_EPSG = 'epsg:26917'  #  NAD83 / UTM zone 17N datum / UTM zone 17N UNIT Meters order long, lat
    #if input_epsg == 'epsg:4326' or input_epsg == 'epsg:6349':  # order lat, Long
    latitude = value_1
    longitude = value_2
    #else:  # order Long, Lat
    #    latitude = value_2
    #    longitude = value_1

    transformer = Transformer.from_crs(input_epsg, output_epsg, always_xy=False)
    X, Y = transformer.transform(longitude, latitude)

    return X, Y


def create_endpoints_360_degrees(longitude, latitude, distance_in_meters):
    #  create the end points that will become the elevations arrays from the DEM
    #  output will be a simple Degree, Start_long, Start_lat, End_long, End_lat
    #  create polygon for subset building database

    Output_DF = pd.DataFrame(
        columns=['Degree', 'StartPoint_Longitude', 'StartPoint_Latitude', 'EndPoint_Longitude', 'EndPoint_Latitude'])
    point_list = []
    for Degree in range(0, 360):  # started at 0 degrees
        EndPoint_Longitude, EndPoint_Latitude = end_point_given_azm_distance(longitude, latitude, Degree, distance_in_meters)
        point = Point(EndPoint_Longitude, EndPoint_Latitude)
        point_list.append(point)
        row = dict(Degree=Degree, StartPoint_Longitude=longitude, StartPoint_Latitude=latitude, EndPoint_Longitude=EndPoint_Longitude, EndPoint_Latitude=EndPoint_Latitude)
        Output_DF = pd.concat([Output_DF, pd.DataFrame([row])])
    polygon = Polygon([[p.x, p.y] for p in point_list])
    Output_DF.reset_index(drop=True, inplace=True)
    return Output_DF, polygon


def catalog_geotifs(dir_name):
    #  this functions makes a library of GEOTIFFS information getting bounds and CRS
    #  get a list of files from the supplied directory
    #  Coord_EPSG = 'epsg:6349'  #  NAD83(2011) datum  all of USA order lat, long set as default
    list_of_files = []
    Output_DF = pd.DataFrame(
        columns=['Name', 'CRS', 'top', 'bottom', 'left', 'right', 'projected_CRS', 'degree_top', 'degree_bottom',
                 'degree_left', 'degree_right'])

    for path in os.listdir(dir_name):
        # check if current path is a file
        if os.path.isfile(os.path.join(dir_name, path)):
            list_of_files.append(path)

    for file in list_of_files:
        tile = rasterio.open(dir_name + "/" + file)
        top = tile.bounds.top
        bottom = tile.bounds.bottom
        left = tile.bounds.left
        right = tile.bounds.right
        meta = tile.meta
        crs = meta['crs']
        Degree_top, Degree_left = epsg_transform_point(left, top, crs, 'epsg:6349')
        Degree_bottom, Degree_right = epsg_transform_point(right, bottom, crs, 'epsg:6349')
        projected_CRS = 'epsg:6349'

        row = dict(Name=file, CRS=crs, top=top, bottom=bottom, left=left, right=right,
                   projected_CRS=projected_CRS, degree_top=Degree_top, degree_bottom=Degree_bottom,
                   degree_left=Degree_left, degree_right=Degree_right)
        Output_DF = pd.concat([Output_DF, pd.DataFrame([row])])
    Output_DF.reset_index(drop=True, inplace=True)

    return Output_DF

def find_geotif_file_names(coord_epsg, x_y_epsg, list_of_geotiff_tiles, longitude, latitude, buffer_distance_meters):
    #  this function adds a buffer zone and compares what file should be returned
    #

    file_names = []
    points_list = []
    # add buffer distance to the point in case we have overlap between tiles
    Degrees_buffer = [0, 45, 90, 135, 180, 225, 270, 315]
    for degree in Degrees_buffer:
        end_point_longitude, end_point_latitude = end_point_given_azm_distance(longitude, latitude, degree,
                                                                               buffer_distance_meters)
        x, y = epsg_transform_point(end_point_longitude, end_point_latitude, coord_epsg, x_y_epsg)
        points_list.append(dict(Degree=degree, distance=buffer_distance_meters, X=x, Y=y))

    x, y = epsg_transform_point(longitude, latitude, coord_epsg, x_y_epsg)  # need to fix this somehow
    points_list.append(dict(Degree=0, distance=0, X=x, Y=y))  # site point

    for point in points_list:
        x = point['X']
        y = point['Y']
        for index in range(0, len(list_of_geotiff_tiles)):
            top = list_of_geotiff_tiles['top'][index]
            bottom = list_of_geotiff_tiles['bottom'][index]
            right = list_of_geotiff_tiles['right'][index]
            left = list_of_geotiff_tiles['left'][index]
            name = list_of_geotiff_tiles['Name'][index]
            # check if our point falls within the tile X first left to right
            if left < x < right:
                if bottom < y < top:
                    file_names.append(name)
    file_names = list(set(file_names))

    return file_names


def list_of_points_360_degrees(polygon_x_y, buffer_distance_meters):
    #  this function creates a list of xy points for all 360 degrees
    n_points = buffer_distance_meters
    list_of_degrees = []

    for degree in range(0, len(polygon_x_y)):
        StartPoint_X = polygon_x_y['StartPoint_X'][degree]
        StartPoint_Y = polygon_x_y['StartPoint_Y'][degree]
        EndPoint_X = polygon_x_y['EndPoint_X'][degree]
        EndPoint_Y = polygon_x_y['EndPoint_Y'][degree]
        list_of_points = []
        point = dict(distance=0, X=StartPoint_X, Y=StartPoint_Y)
        list_of_points.append(point)

        for index in np.arange(1, n_points + 1):
            x_dist = EndPoint_X - StartPoint_X
            y_dist = EndPoint_Y - StartPoint_Y
            x = (StartPoint_X + (x_dist / (n_points + 1)) * index)
            y = (StartPoint_Y + (y_dist / (n_points + 1)) * index)
            point = dict(distance=index, X=x, Y=y)
            list_of_points.append(point)
        point = dict(distance=len(list_of_points) + 1, X=EndPoint_X, Y=EndPoint_Y)
        list_of_points.append(point)
        list_of_degrees.append(list_of_points)

    return list_of_degrees


def list_of_ground_elevations_points_360_degrees(list_of_degrees, tile):
    Ground_Elevation: list[Any] = []
    List_of_Degrees_Ground_Elevation: list[Any] = []
    dem_data = tile.read(1)

    for degree in range(0, len(list_of_degrees)):
        Ground_Elevation: list[Any] = []
        one_degree = list_of_degrees[degree]
        for index in range(0, len(one_degree)):
            x = one_degree[index]['X']
            y = one_degree[index]['Y']
            row, col = tile.index(x, y)
            Ground_Elevation.append(round(dem_data[row, col], 1))
        #  print(Ground_Elevation[499])
        List_of_Degrees_Ground_Elevation.append(Ground_Elevation)
    return List_of_Degrees_Ground_Elevation


def find_geotif_boundaries(file_name):
    #  this function returns a geo tiff CRS and boundaries all
    tile = rasterio.open(file_name)
    top = tile.bounds.top
    bottom = tile.bounds.bottom
    left = tile.bounds.left
    right = tile.bounds.right
    meta = tile.meta
    crs = meta['crs']
    return tile, crs, top, bottom, right, left


def create_tile_subset_from_state_building_geojson(list_of_geotif_tiles_df, path_building_geojson, subset_path_gpkg, subset_path_json):
    # check to see if we need to create building tiles

    load_building_GEOJSON = False
    #  check for missing files create them if needed
    index = 0
    while (index < len(list_of_geotif_tiles_df)) and not load_building_GEOJSON:
        file_name_gpkg = list_of_geotif_tiles_df['Name'][index]
        file_name_gpkg = file_name_gpkg.replace(".tif", "_building.gpkg")
        full_path_gpkg = subset_path_gpkg + file_name_gpkg
        file_name_json = list_of_geotif_tiles_df['Name'][index]
        file_name_json = file_name_json.replace(".tif", "_building.geojson")
        full_path_json = subset_path_json + file_name_json
        index = index + 1
        if not os.path.isfile(full_path_gpkg):
            load_building_GEOJSON = True
        if not os.path.isfile(full_path_json):
            load_building_GEOJSON = True

    if load_building_GEOJSON:
        GDF = gpd.read_file(path_building_geojson)
        GDF = GDF.set_crs('epsg:6349', allow_override=True)

        for index in range(0, len(list_of_geotif_tiles_df)):
            file_name_gpkg = list_of_geotif_tiles_df['Name'][index]
            file_name_gpkg = file_name_gpkg.replace(".tif", "_building.gpkg")
            full_path_gpkg = subset_path_gpkg + file_name_gpkg
            file_name_json = list_of_geotif_tiles_df['Name'][index]
            file_name_json = file_name_json.replace(".tif", "_building.geojson")
            full_path_json = subset_path_json + file_name_json
            top = list_of_geotif_tiles_df['degree_top'][index]
            bottom = list_of_geotif_tiles_df['degree_bottom'][index]
            left = list_of_geotif_tiles_df['degree_left'][index]
            right = list_of_geotif_tiles_df['degree_right'][index]
            polygon = Polygon([(left, top), (right, top), (right, bottom), (left, bottom), (left, top)])
            poly_gdf = gpd.GeoDataFrame([1], geometry=[polygon], crs='epsg:6349')
            subset_area = GDF.clip(poly_gdf)
            subset_area.reset_index(drop=True, inplace=True)
            subset_area.to_file(full_path_gpkg, driver='GPKG', layer='Buildings', crs='epsg:6349')
            subset_area.to_file(full_path_json, driver='GeoJSON')

    return

def catalog_lidar_geotifs(dir_name, path_State_shp, path_County_shp, path_Urban_Area_shp):
    # Glen Ossman updated on 5/3/2023 this function takes all the LIDAR files and creates a single coverage file
    # this is useful in finding missing data
    list_of_files = []

    # load in our .shp file it is by state
    if os.path.isfile(path_State_shp):
        GeoDataFrameState = gpd.read_file(path_State_shp)
        EPSG_Code_State = GeoDataFrameState.crs
        EPSG_Code_State = EPSG_Code_State.srs
    else:
        print("State .shp File not found @ " + path_State_shp)
        sys.exit("State .shp File not found @ " + path_State_shp)

    # load in our .shp file it is by County
    if os.path.isfile(path_County_shp):
        GeoDataFrameCounty = gpd.read_file(path_County_shp)
        EPSG_Code_County = GeoDataFrameCounty.crs.geodetic_crs
        EPSG_Code_County = EPSG_Code_County.srs # trim this down to just epsg code
        Start = EPSG_Code_County.find('ID["EPSG",')
        if Start > 0:
            substring = EPSG_Code_County[Start:len(EPSG_Code_County) - 1]
            substring = substring.replace('ID["EPSG",', '')
            substring = substring.replace(']', '')
            EPSG_Code_County = "epsg:" + substring
        else:
            print("Unable to get EPS code from data from " + path_County_shp)
            sys.exit("Unable to get EPS code from data from " + path_County_shp)
    else:
        print("State .shp File not found @ " + path_County_shp)
        sys.exit("State .shp File not found @ " + path_County_shp)

    # load in our JSON file it is by Urban_Area
    if os.path.isfile(path_Urban_Area_shp):
        GeoDataFrameUrban_Area = gpd.read_file(path_County_shp)
        EPSG_Code_Urban_Area = GeoDataFrameUrban_Area.crs.geodetic_crs
        EPSG_Code_Urban_Area = EPSG_Code_Urban_Area.srs
        if Start > 0:
            substring = EPSG_Code_Urban_Area[Start:len(EPSG_Code_Urban_Area) - 1]
            substring = substring.replace('ID["EPSG",', '')
            substring = substring.replace(']', '')
            EPSG_Code_Urban_Area = "epsg:" + substring
        else:
            print("Unable to get EPS code from data from " + path_Urban_Area_shp)
            sys.exit("Unable to get EPS code from data from " + path_Urban_Area_shp)
    else:
        print("Urban_Area .shp File not found @ " + path_Urban_Area_shp)
        sys.exit("Urban_Area .shp File not found @ " + path_Urban_Area_shp)

    for path in os.listdir(dir_name):
        # check if current path is a file
        if os.path.isfile(os.path.join(dir_name, path)):
            list_of_files.append(path)
        else:
            print(" LIDAR Dir not found " + dir_name)
            sys.exit("LIDAR Dir not found " + dir_name)

    for file in list_of_files:
        if file[-4:] == ".laz":
            las = laspy.read(dir_name + "/" + file)
            crs = las.vlrs[2] # let get the CRS value using some header information
            crs = crs.strings[0]
            x_max = las.header.x_max
            x_min = las.header.x_min
            y_max = las.header.y_max
            y_min = las.header.y_min
            polygon = Polygon([(x_min, y_max), (x_max, y_max), (x_max, y_min), (x_min, y_min)])
            midpoint_x = (x_max + x_min) / 2
            midpoint_y = (y_max + y_min) / 2
            EPSG_Code = 0  # set code to default in case we have bad data
            if crs[0:21] == "NAD_1983_UTM_Zone_10N":
                EPSG_Code = 26910
            if crs[0:21] == "NAD_1983_UTM_Zone_11N":
                EPSG_Code = 26911
            if crs[0:21] == "NAD_1983_UTM_Zone_12N":
                EPSG_Code = 26912
            if crs[0:21] == "NAD_1983_UTM_Zone_13N":
                EPSG_Code = 26913
            if crs[0:21] == "NAD_1983_UTM_Zone_14N":
                EPSG_Code = 26914
            if crs[0:21] == "NAD_1983_UTM_Zone_15N":
                EPSG_Code = 26915
            if crs[0:21] == "NAD_1983_UTM_Zone_16N":
                EPSG_Code = 26916
            if crs[0:21] == "NAD_1983_UTM_Zone_17N":
                EPSG_Code = 26917
            if crs[0:21] == "NAD_1983_UTM_Zone_18N":
                EPSG_Code = 26918
            if crs[0:21] == "NAD_1983_UTM_Zone_19N":
                EPSG_Code = 26919
            if crs[0:21] == "NAD_1983_UTM_Zone_20N":
                EPSG_Code = 26920
            if crs[0:21] == "NAD_1983_UTM_Zone_21N":
                EPSG_Code = 26921
            Y, X = epsg_transform_point(midpoint_y, midpoint_x, EPSG_Code, EPSG_Code_State)
            point = Point(X, Y)

            state = ''
            index = 0
            while index < len(GeoDataFrameState) and len(state) == 0:
                if point.within(GeoDataFrameState.iloc[index]["geometry"]):
                    state = GeoDataFrameState.iloc[index]["STUSPS"]
                index = index + 1

            County = ''
            index = 0
            while index < len(GeoDataFrameCounty) and len(County) == 0:
                if point.within(GeoDataFrameCounty.iloc[index]["geometry"]):
                    County = GeoDataFrameCounty.iloc[index]["NAME"]
                index = index + 1

            Urban_Area = ''
            index = 0
            while index < len(GeoDataFrameUrban_Area) and len(Urban_Area) == 0:
                if point.within(GeoDataFrameUrban_Area.iloc[index]["geometry"]):
                    Urban_Area = GeoDataFrameUrban_Area.iloc[index]["NAME"]
                index = index + 1

            data = {'File_Name':[file], 'State': [state], 'CRS_Name': [crs], 'EPSG_Code': [EPSG_Code], 'x_max': [x_max], 'x_min': [x_min], 'y_max': [y_max],'y_min': [y_min]}
            df = pd.DataFrame(data)

            reprojected_GeoDataFrameState = GeoDataFrameState.to_crs(epsg=EPSG_Code)



            #polygon_GEO_DF = gpd.GeoDataFrame(columns=["File_Name", 'State', 'CRS', 'x_max', 'x_min', 'y_max', 'y_min', "geometry"], crs=crs, geometry="geometry")

            #poly_gdf = gpd.GeoDataFrame(df, crs=crs, geometry=[polygon])
            #polygon_GEO_DF = pd.concat([polygon_GEO_DF, poly_gdf])

    return



def catalog_lidar_geotifs_Polygon(dir_name, crs):
    # Glen Ossman updated on 5/3/2023 this function takes all the LIDAR files and creates a single coverage file
    # this is useful in finding missing data
    list_of_files = []

    polygon_GEO_DF = gpd.GeoDataFrame(columns=["File_Name", "geometry"], crs=crs, geometry="geometry")

    for path in os.listdir(dir_name):
        # check if current path is a file
        if os.path.isfile(os.path.join(dir_name, path)):
            list_of_files.append(path)

    for file in list_of_files:
        if file[-4:] == ".laz":
            las = laspy.read(dir_name + "/" + file)
            x_max = las.header.x_max
            x_min = las.header.x_min
            y_max = las.header.y_max
            y_min = las.header.y_min
            polygon = Polygon([(x_min, y_max), (x_max, y_max), (x_max, y_min), (x_min, y_min)])
            data = {'File_Name': [file]}
            df = pd.DataFrame(data)
            poly_gdf = gpd.GeoDataFrame(df, crs=crs, geometry=[polygon])
            polygon_GEO_DF = pd.concat([polygon_GEO_DF, poly_gdf])

    return polygon_GEO_DF


