import os
import pandas as pd
import requests
import time
from os import walk

# import a list of files from https://apps.nationalmap.gov/downloader/
# Elevation Source Data (3DEP) - Tiff
# Create a shopping cart and save as a CSV file
# Column O should have the web address of the file it should look something like this
# "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/MD_Western_2021_D21/Tiff/USGS_1M_17_x75y437_MD_Western_2021_D21.tif"

def Download_from_Cart_GeoTiff(ShoppingCart, OneMeterGeoTiff_directory):

    # Step 1 get a list of GeoTiff file we have
    All_files_in_GeoTiff_REPO = []
    for (dir_path, dir_names, file_names) in walk(OneMeterGeoTiff_directory):
        All_files_in_GeoTiff_REPO.extend(file_names)
    list_of_files_in_GeoTiff_REPO = []
    for file in All_files_in_GeoTiff_REPO:
        if file[-4:] == ".tif":
            list_of_files_in_GeoTiff_REPO.append(file)
    print("Number of Files currently in GeoTiff REPO = {}".format(len(list_of_files_in_GeoTiff_REPO)))

    # Step 2 open CSV file that contains or shopping Cart
    GeoTiff_Shopping_Cart_DF = pd.read_csv(ShoppingCart, header=None)
    # looks like 17 contains the URL we need
    # convert it to a list
    GeoTiff_URL_list = list(GeoTiff_Shopping_Cart_DF[14])
    # were going to create a new dataframe from 2 list using a for loop
    GeoTiff_file_name = []
    for URL in GeoTiff_URL_list:
        GeoTiff_file_name.append(URL.rsplit('/', 1)[1])
    GeoTiff_URL_list_DF = pd.DataFrame(list(zip(GeoTiff_file_name, GeoTiff_URL_list)), columns=['file_name', 'URL'])
    GeoTiff_URL_list_DF['Download'] = False
    print("Number of Links in Shopping cart = {}".format(len(GeoTiff_URL_list_DF)))

    # Step 3 compare list to create our dataframe of needed downloads setting Column Download to True
    for index in GeoTiff_URL_list_DF.index:
        if GeoTiff_URL_list_DF["file_name"][index] not in list_of_files_in_GeoTiff_REPO:
            GeoTiff_URL_list_DF.at[index, "Download"] = True

    # Step 4 now create a list of only files we want to download
    # select from data frame only rows where download = true
    GeoTiff_URL_list_DF = GeoTiff_URL_list_DF.loc[GeoTiff_URL_list_DF['Download'] == True]
    List_of_URL_to_download = list(GeoTiff_URL_list_DF['URL'])
    print("Number of Files to Download GeoTiff = {}".format(len(List_of_URL_to_download)))

    # Step 5 download our files
    for URL in List_of_URL_to_download:
        if URL.find('/'):
            file_name = URL.rsplit('/', 1)[1]
            file_name = OneMeterGeoTiff_directory + file_name
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

    return


def Sort_GeoTiffR(OneMeterGeoTiff_directory):
    # Step 1 get a list of LIDAR file we have
    All_files_in_GeoTiff_REPO = os.listdir(OneMeterGeoTiff_directory)
    print("Number of Files currently in LIDAR REPO = {}".format(len(All_files_in_GeoTiff_REPO)))
    for file in All_files_in_GeoTiff_REPO:

        if file[-4:] == ".laz":
            #las = laspy.read(LIDAR_directory + file)
            crs = ""
    return