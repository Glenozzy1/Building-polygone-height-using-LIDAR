# Glen Ossman started on 8/29/2023 rev 1
# this function check LAZ repo and XML repo to build a CRC grid information and point for tile polygon
# we create a dataframe with all the catalog information
# add update to database
import os
from os import walk
import pandas as pd
import laspy
from bs4 import BeautifulSoup
import geopandas
import re

def ListOfFilesinREPO(LIDAR_XML, LIDAR_directory):

    # get a list of Lidar files we have
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

    # get a list of all file in XML REPO
    list_LIDAR_XML = os.listdir(LIDAR_XML)
    list_of_files_in_XML_REPO = []
    for file in list_LIDAR_XML:
        if file[-4:] == ".xml":
            # Strip off the .xml so we can use it on XML list
            file = file.replace(".xml", "")
            list_of_files_in_XML_REPO.append(file)

    print("Number of Files currently in LIDAR REPO = {}".format(len(list_of_files_in_XML_REPO)))

    CompleteFileList = list_of_files_in_LIDAR_REPO + list_of_files_in_XML_REPO  # combine list
    CompleteFileList = list(set(CompleteFileList))  # remove duplicates
    REPO_DF = pd.DataFrame(CompleteFileList)
    REPO_DF.columns = ['File_Name']

    REPO_DF['EPSG_H'] = ""
    REPO_DF['EPSG_V'] = ""
    REPO_DF['UNIT'] = ""
    REPO_DF['XML_file'] = False
    REPO_DF['LAZ_file'] = False
    REPO_DF['westbc'] = 0
    REPO_DF['eastbc'] = 0
    REPO_DF['northbc'] = 0
    REPO_DF['southbc'] = 0
    REPO_DF['x_max'] = 0
    REPO_DF['x_min'] = 0
    REPO_DF['y_max'] = 0
    REPO_DF['y_min'] = 0
    REPO_DF['gridsysn'] = 0
    REPO_DF['utmzone'] = 0
    REPO_DF['horizdn'] = ""
    REPO_DF['ellips'] = ""
    REPO_DF['altdatum'] = ""
    REPO_DF['State'] = ""
    REPO_DF['County'] = ""
    REPO_DF['Region'] = ""
    REPO_DF['Town'] = ""
    REPO_DF['crs'] = ""
    REPO_DF['empty'] = ""


    for index in REPO_DF.index:
        FullFilePath = LIDAR_directory + REPO_DF.iloc[index]['File_Name'] + ".laz"
        if os.path.isfile(FullFilePath):
            las = laspy.read(LIDAR_directory + REPO_DF.iloc[index]['File_Name'] + ".laz")
            REPO_DF.at[index, "LAZ_file"] = True
            crs = ""
            if len(las.vlrs) == 0:
                crs = "No Info"
            else:
                if hasattr(las.vlrs[0], 'string'):
                    # obj.attr_name exists.
                    crs = las.vlrs[0].string  # let get the CRS value using some header information
                elif hasattr(las.vlrs[0], 'strings'):
                    # obj.attr_name exists.
                    crs = las.vlrs[0].strings[0]  # let get the CRS value using some header information
                if not crs:
                    if len(las.vlrs) > 0:
                        if hasattr(las.vlrs[1], 'string'):
                            # obj.attr_name exists.
                            crs = las.vlrs[1].string  # let get the CRS value using some header information
                        elif hasattr(las.vlrs[1], 'strings'):
                            # obj.attr_name exists.
                            crs = las.vlrs[1].strings[0]  # let get the CRS value using some header information
                if not crs:
                    if len(las.vlrs) > 1:
                        if hasattr(las.vlrs[2], 'string'):
                            # obj.attr_name exists.
                            crs = las.vlrs[2].string  # let get the CRS value using some header information
                        elif hasattr(las.vlrs[2], 'strings'):
                            # obj.attr_name exists.
                            crs = las.vlrs[2].strings[0]  # let get the CRS value using some header information
                REPO_DF.at[index, "crs"] = crs
                if re.search('US Survey foot', crs, re.IGNORECASE):
                    REPO_DF.at[index, "UNIT"] = 'Feet'
                else:
                    REPO_DF.at[index, "UNIT"] = 'Meters'
                #temp = crs.split(",")
                # decoding crs string into EPSG
                crs = crs.replace(',AUTHORITY["EPSG",', ',AUTHORITY["EPSG" ')
                VERT = crs.find("VERT")
                HOZ_crs = crs[0: VERT]  # remove Vertical EPSG
                VERT_crs = crs[VERT:]  # remove Horizontal EPSG
                ListToSearchforHOZ_ESPG = HOZ_crs.split(",")
                ListToSearchforVERT_ESPG = VERT_crs.split(",")
                listOfEPSG_HOZ = [x for x in ListToSearchforHOZ_ESPG if 'AUTHORITY' in x]
                listOfEPSG_VERT = [x for x in ListToSearchforVERT_ESPG if 'AUTHORITY' in x]
                if len(listOfEPSG_HOZ) > 0:
                    temp = listOfEPSG_HOZ.pop()
                    temp = temp.replace(']]', ']" ')
                    temp = temp.replace('"', '')
                    temp = int(''.join(filter(str.isdigit, temp)))
                    REPO_DF.at[index, "EPSG_H"] = 'epsg' + str(temp)

                else:
                    REPO_DF.at[index, "EPSG_H"] = "Not Found in laz file"

                if len(listOfEPSG_VERT) > 0:
                    temp = listOfEPSG_VERT.pop()
                    temp = temp.replace(']]', ']" ')
                    temp = temp.replace('"', '')
                    temp = int(''.join(filter(str.isdigit, temp)))
                    REPO_DF.at[index, "EPSG_V"] = 'epsg' + str(temp)

                else:
                    REPO_DF.at[index, "EPSG_V"] = "Not Found in laz file"

                if hasattr(las.header, 'x_max'):
                    REPO_DF.at[index, "x_max"] = las.header.x_max
                    REPO_DF.at[index, "x_min"] = las.header.x_min
                    REPO_DF.at[index, "y_max"] = las.header.y_max
                    REPO_DF.at[index, "y_min"] = las.header.y_min
        else:
            REPO_DF.at[index, "LAZ_file"] = False
        # ******************************** Start XML ******************************************************8
        FullFilePath = LIDAR_XML + REPO_DF.iloc[index]['File_Name'] + ".xml"
        if os.path.isfile(FullFilePath):
            REPO_DF.at[index, "XML_file"] = True
            with open(FullFilePath, 'r') as f:
                data = f.read()
            bs_data = BeautifulSoup(data, 'lxml')
            westbc = float(bs_data.find('westbc').text)
            eastbc = float(bs_data.find('eastbc').text)
            northbc = float(bs_data.find('northbc').text)
            southbc = float(bs_data.find('southbc').text)
            gridsysn = ""
            utmzone = ""
            horizdn = ""
            ellips = ""
            altdatum = ""
            if bs_data.find('gridsysn'):
                gridsysn = bs_data.find('gridsysn').text
            if bs_data.find('utmzone'):
                utmzone = int(bs_data.find('utmzone').text)
            if bs_data.find('horizdn'):
                horizdn = bs_data.find('horizdn').text
            if bs_data.find('ellips'):
                ellips = bs_data.find('ellips').text
            if bs_data.find('altdatum'):
                altdatum = bs_data.find('altdatum').text
            REPO_DF.at[index, "westbc"] = westbc
            REPO_DF.at[index, "eastbc"] = eastbc
            REPO_DF.at[index, "northbc"] = northbc
            REPO_DF.at[index, "southbc"] = southbc
            REPO_DF.at[index, "gridsysn"] = gridsysn
            REPO_DF.at[index, "utmzone"] = utmzone
            REPO_DF.at[index, "horizdn"] = horizdn
            REPO_DF.at[index, "ellips"] = ellips
            REPO_DF.at[index, "altdatum"] = altdatum
        else:
            REPO_DF.at[index, "XML_file"] = False



    #gdf = geopandas.GeoDataFrame(REPO_DF, geometry=geopandas.points_from_xy(df.Longitude, df.Latitude), crs="EPSG:4326")

    return
