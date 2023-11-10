import os
#import numpy as np
#import laspy
import pandas as pd
from geopandas import gpd
#from shapely.geometry import Point, Polygon
import requests
import time
import Create_catalog
import GEO_Functions
import Download_LIDAR
import Download_1MeterTIFF


# import a list of files from https://apps.nationalmap.gov/downloader/
# Elevation Source Data (3DEP) - Lidar, IfSAR
# Create a shopping cart and save as a CSV file
# Column R should have the web address of the file it should look something like this
# "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/USGS_Lidar_Point_Cloud_NJ_SdL5_2014_LAS_2015/laz/18TWK610835.laz"
# Point the software to the location of the file

ShoppingCart_LIDAR = "/media/glen/GIS_Data/USGS_Shopping_Cart/"
LIDAR_directory = "/media/glen/GIS_Data/Lidar/"
LIDAR_XML = "/media/glen/GIS_Data/Lidar_XML/"


#LIDAR_directory = "/home/glen/TestData/"
#LIDAR_XML = "/home/glen/TestData/"


ShoppingCart_GeoTIFF = "/media/glen/GIS_Data/1_Meter_GEOTIFF/data.csv"
OneMeterGeoTIFF_directory = "/media/glen/GIS_Data/1_Meter_GEOTIFF/"
path_building_geojson = '/media/glen/GIS_Data/Building_Polygons/Building GEO-JSON/Virginia.geojson'
LIDAR_Coverage_Polygons_DIR = "/media/glen/GIS_Data/LIDAR_Coverage_Polygons/"
path_State_geojson = "/media/glen/GIS_Data/US_States/us_state_20m.shp"
path_County_geojson = "/media/glen/GIS_Data/us_county/us_county_20m.shp"
path_Urban_Area_geojson = "/media/glen/GIS_Data/Urban Areas/us_ua10_500k.shp"

if __name__ == '__main__':
    #Create_catalog.ListOfFilesinREPO(LIDAR_XML, LIDAR_directory)


    Download_LIDAR.Download_from_Cart_LIDAR(ShoppingCart_LIDAR, LIDAR_XML, LIDAR_directory)
    # Download_LIDAR.Sort_LIDAR(LIDAR_directory)
#    Download_1MeterTIFF. Download_from_Cart_GeoTiff(ShoppingCart_GeoTIFF, OneMeterGeoTIFF_directory)

  #  GEO_Functions.catalog_geotifs(OneMeterGeoTIFF_directory)



    # Step 6 create polygons and save them as gpkg files to see what area are covered
    #Coverage_polygon = GEO_Functions.catalog_lidar_geotifs(LIDAR_directory, path_State_geojson, path_County_geojson, path_Urban_Area_geojson)
    #Coverage_polygon.to_file(filename= LIDAR_Coverage_Polygons_DIR + "Lidar.gpkg", driver="GPKG", layer='lidar_tiles')

    # Step 7 reload file list for LIDAR_directory we need to process the new ones
    #list_of_files_in_LIDAR_REPO = []
    #for file in os.listdir(LIDAR_directory):
    #    # check if current path is a file
    #    if os.path.isfile(os.path.join(LIDAR_directory, file)):
    #        if file[-4:] == ".laz":
    #            list_of_files_in_LIDAR_REPO.append(file)





    ## load in our JSON file it is by state
    #if os.path.isfile(path_building_geojson):
    #    GeoDataFrame = gpd.read_file(path_building_geojson)
    #    reprojected_GeoDataFrame = GeoDataFrame.to_crs(epsg=26917)
    #else:
    #    print("Building JSON File not found @ " + path_building_geojson)


























