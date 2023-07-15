import os
import pandas as pd
import requests
import time

# import a list of files from https://apps.nationalmap.gov/downloader/
# Elevation Source Data (3DEP) - Lidar, IfSAR
# Create a shopping cart and save as a CSV file
# Column R should have the web address of the file it should look something like this
# "https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/USGS_Lidar_Point_Cloud_NJ_SdL5_2014_LAS_2015/laz/18TWK610835.laz"
# Point the software to the location of the file

ShoppingCart = "/media/glen/GIS_Data/Lidar/data.csv"
LIDAR_directory = "/media/glen/GIS_Data/Lidar/"
#path_building_geojson = '/media/glen/GIS_Data/Building_Polygons/Building GEO-JSON/Virginia.geojson'
#LIDAR_Coverage_Polygons_DIR = "/media/glen/GIS_Data/LIDAR_Coverage_Polygons/"
#path_State_geojson = "/media/glen/GIS_Data/US_States/us_state_20m.shp"
#path_County_geojson = "/media/glen/GIS_Data/us_county/us_county_20m.shp"
#path_Urban_Area_geojson = "/media/glen/GIS_Data/Urban Areas/us_ua10_500k.shp"

if __name__ == '__main__':
    # Step 1 get a list of LIDAR file we have
    list_of_files_in_LIDAR_REPO = []
    for file in os.listdir(LIDAR_directory):
        # check if current path is a file
        if os.path.isfile(os.path.join(LIDAR_directory, file)):
            if file[-4:] == ".laz":
                list_of_files_in_LIDAR_REPO.append(file)

    # Step 2 open CSV file that contains or shopping Cart
    LIDAR_Shopping_Cart_DF = pd.read_csv(ShoppingCart, header=None)
    # looks like 20 contains the URL we need
    # convert it to a list
    LIDAR_URL_list = list(LIDAR_Shopping_Cart_DF[17])
    # were going to create a new dataframe from 2 list using a for loop
    LIDAR_file_name = []
    for URL in LIDAR_URL_list:
        LIDAR_file_name.append(URL.rsplit('/', 1)[1])
    LIDAR_URL_list_DF = pd.DataFrame(list(zip(LIDAR_file_name, LIDAR_URL_list)), columns=['file_name', 'URL'])
    LIDAR_URL_list_DF['Download'] = False

    # Step 3 compare list to create our dataframe of needed downloads setting Column Download to True
    for index in LIDAR_URL_list_DF.index:
        if LIDAR_URL_list_DF["file_name"][index] not in list_of_files_in_LIDAR_REPO:
            LIDAR_URL_list_DF.at[index, "Download"] = True

    # Step 4 now create a list of only files we want to download
    # select from data frame only rows where download = true
    LIDAR_URL_list_DF = LIDAR_URL_list_DF.loc[LIDAR_URL_list_DF['Download'] == True]
    List_of_URL_to_download = list(LIDAR_URL_list_DF['URL'])
    del (LIDAR_Shopping_Cart_DF, LIDAR_file_name, LIDAR_URL_list_DF, LIDAR_URL_list, list_of_files_in_LIDAR_REPO, ShoppingCart)

    # Step 5 download our files
    for URL in List_of_URL_to_download:
        if URL.find('/'):
            file_name = URL.rsplit('/', 1)[1]
            file_name = LIDAR_directory + file_name
            try:
                r = requests.get(URL, allow_redirects=True)
            except IOError as e:
                print("An error occurred:", e)
                time.sleep(30)  # Sleep for 30 seconds
                r = requests.get(URL, allow_redirects=True)
            if r.reason == 'Service Unavailable':
                print("URL=" + URL + ' Service Unavailable')
            else:  # I don't like the logic on this will look into changing
                open(file_name, 'wb').write(r.content)
                print("File " + file_name + " added to REPO")
            time.sleep(5)  # Sleep for 2 seconds
