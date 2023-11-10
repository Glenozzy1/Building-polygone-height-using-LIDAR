import os
import pandas as pd
import requests
import time
from os import walk
import multiprocessing as mp


# from shapely.geometry import Polygon, Point

# import a list of files from https://apps.nationalmap.gov/downloader/
# Elevation Source Data (3DEP) - Lidar, IfSAR
# Create a shopping cart and save as a CSV file
# Column R should have the web address of the file it should look something like this
# "S_Lidar_Point_Cloud_NJ_SdL5_2014_LAS_https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/USG2015/laz/18TWK610835.laz"
# Point the software to the location of the file


def Multiprocessing_Download(URL, file_name):
    try:
        r = requests.get(URL, allow_redirects=True)
    except IOError as e:
        print("An error occurred:", e)
        time.sleep(30)  # Sleep for 30 seconds
        r = requests.get(URL, allow_redirects=True)
    if r.reason == 'Service Unavailable':
        print("URL=" + URL + ' Service Unavailable')
    elif r.status_code == 200:
        open(file_name, 'wb').write(r.content)
        print("File " + file_name + " added to REPO")
    elif r.status_code == 404:
        print("URL=" + URL + ' File not found Error 404')
    else:
        print("An error occurred:", e)
    return


def Download_from_Cart_LIDAR(ShoppingCart, LIDAR_XML, LIDAR_directory):
    dir_list_ShoppingCart = os.listdir(ShoppingCart)
    MasterList = pd.DataFrame(columns=['Name', 'XML_Link', 'Catalog', 'File_Link', 'Last_Update'])

    for file in dir_list_ShoppingCart:
        if ".csv" in file:
            LIDAR_Shopping_Cart_DF = pd.read_csv(ShoppingCart + file, header=None)
            LIDAR_Shopping_Cart_DF = LIDAR_Shopping_Cart_DF[[0, 4, 6, 14, 24]]
            LIDAR_Shopping_Cart_DF.columns = ['Name', 'XML_Link', 'Catalog', 'File_Link', 'Last_Update']
            MasterList = pd.concat([MasterList, LIDAR_Shopping_Cart_DF])

    # Step 1 get a list of Lidar files we have
    All_files_in_LIDAR_REPO = []
    for (dir_path, dir_names, file_names) in walk(LIDAR_directory):
        All_files_in_LIDAR_REPO.extend(file_names)
    list_of_files_in_LIDAR_REPO = []
    for file in All_files_in_LIDAR_REPO:
        if file[-4:] == ".laz":
            # Strip off the .laz so we can use it on XML list
            file = file.replace(".laz", "")
            list_of_files_in_LIDAR_REPO.append(file)
    print("Number of Files currently in LIDAR REPO = {}".format(len(list_of_files_in_LIDAR_REPO)))

    # Step 3 compare list to create our dataframe of needed downloads setting Column Download to True
    # LAZ files
    MasterList.reset_index()
    MasterList['Download_LAZ'] = None
    for index in MasterList.index:
        Just_File_Name = os.path.basename(MasterList.iloc[index]['File_Link'])
        MasterList.at[index, 'Name'] = Just_File_Name.replace(".laz", "")
        if MasterList.iloc[index]['Name'] not in list_of_files_in_LIDAR_REPO:
            MasterList.at[index, "Download_LAZ"] = True
        else:
            MasterList.at[index, "Download_LAZ"] = False

    # get a list of all file in XML REPO
    list_LIDAR_XML = os.listdir(LIDAR_XML)
    list_of_files_in_XML_REPO = []
    for file in list_LIDAR_XML:
        if file[-4:] == ".xml":
            # Strip off the .xml so we can use it on XML list
            file = file.replace(".xml", "")
            list_of_files_in_XML_REPO.append(file)

    # we need to fix the XML links by replacing LAZ with Metadata
    # format of request
    # https://www.sciencebase.gov/catalog/item/download/64390eb1d34ee8d4ade0af15?format = json"
    # https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/IL_4_County_QL1_LiDAR_2016_B16/IL_4County_Kane_2018/metadata/USGS_LPC_IL_4_County_QL1_LiDAR_2016_B16_LAS_00008175.xml
    # https://rockyweb.usgs.gov/vdelivery/Datasets/Staged/Elevation/LPC/Projects/IL_4_County_QL1_LiDAR_2016_B16/IL_4County_Kane_2018/LAZ/USGS_LPC_IL_4_County_QL1_LiDAR_2016_B16_LAS_00759725.laz

    MasterList['Download_XML'] = None
    for index in MasterList.index:
        if MasterList.iloc[index]['Name'] in list_of_files_in_XML_REPO:
            MasterList.at[index, "Download_XML"] = False
        else:
            MasterList.at[index, "Download_XML"] = True

    for index in MasterList.index:
        LAZ_Link = MasterList.iloc[index]['File_Link']
        XML_Link = ""
        if "/LAZ/" in LAZ_Link:  # upper lower case problems on linux
            XML_Link = LAZ_Link.replace("/LAZ/", "/metadata/")
        if "/laz/" in LAZ_Link:
            XML_Link = LAZ_Link.replace("/laz/", "/metadata/")
        XML_Link = XML_Link.replace(".laz", "_meta.xml")
        MasterList.at[index, "XML_Link"] = XML_Link

    # Step 5 download our files
    # for index in MasterList.index:
    #     if MasterList.iloc[index]["Download_XML"]:
    #         URL = MasterList.iloc[index]["XML_Link"]
    #         if URL.find('/'):
    #             file_name = LIDAR_XML + MasterList.iloc[index]['Name'] + ".xml"
    #             try:
    #                 r = requests.get(URL, allow_redirects=True)
    #             except IOError as e:
    #                 print("An error occurred:", e)
    #                 time.sleep(30)  # Sleep for 30 seconds
    #                 r = requests.get(URL, allow_redirects=True)
    #             if r.reason == 'Service Unavailable':
    #                 print("URL=" + URL + ' Service Unavailable')
    #             elif r.status_code == 200:
    #                 open(file_name, 'wb').write(r.content)
    #                 print("File " + file_name + " added to REPO")
    #             elif r.status_code == 404:
    #                 URL = URL.replace("_meta.xml", ".xml")
    #                 try:
    #                     r = requests.get(URL, allow_redirects=True)
    #                 except IOError as e:
    #                     print("An error occurred:", e)
    #                 if r.status_code == 200:
    #                     open(file_name, 'wb').write(r.content)
    #                     print("File " + file_name + " added to REPO")
    #             else:
    #                 print("An error occurred:", e)

    # ***********************************************************************************************************



    for index in MasterList.index:
        if MasterList.iloc[index]["Download_LAZ"]:
            URL = MasterList.iloc[index]["File_Link"]
            if URL.find('/'):
                file_name = LIDAR_directory + MasterList.iloc[index]['Name'] + ".laz"

                # try:
                #    r = requests.get(URL, allow_redirects=True)
                # except IOError as e:
                #    print("An error occurred:", e)
                #    time.sleep(30)  # Sleep for 30 seconds
                #    r = requests.get(URL, allow_redirects=True)
                # if r.reason == 'Service Unavailable':
                #    print("URL=" + URL + ' Service Unavailable')
                # elif r.status_code == 200:
                #    open(file_name, 'wb').write(r.content)
                #    print("File " + file_name + " added to REPO")
                # elif r.status_code == 404:
                #    URL = URL.replace("_meta.xml", ".xml")
                # try:
                #    r = requests.get(URL, allow_redirects=True)
                # except IOError as e:
                #    print("An error occurred:", e)
                # if r.status_code == 200:
                #    open(file_name, 'wb').write(r.content)
                #    print("File " + file_name + " added to REPO")
                # else:
                #    print("An error occurred:", e)



    return
