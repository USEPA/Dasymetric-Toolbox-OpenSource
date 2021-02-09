# -*- coding: utf-8 -*-
"""
Name: Open source Intelligent Dasymetric Mapping (IDM) script

Author: Anam Khan

Date: 5/1/19

Description: Intelligent Dasymetric Mapping (IDM) disaggregates population 
counts enumerated by vector source units to the spatial resolution of a 
categorical ancillary raster containing classes that are indicative of the 
spatial distribution of population within the source units. This script is 
an open source version of the EnviroAtlas IDM toolbox developed by 
Torrin Hultgren for ArcMap: https://www.epa.gov/enviroatlas/dasymetric-toolbox.
This version follows the publication by Mennis and Hultgren (2006) with the
exception that class densities for unsampled ancillary classes are calculated
using census polygons where the population estimated for sampled/preset 
ancillary classes did not exceed the census population.
"""

import os, sys, json
from osgeo import gdal, ogr
import numpy as np
import pandas as pd
import geopandas as gp
import argparse as ap


#IDM function
def dasy_map (popFeat_path, popCountField, popKeyField, ancRaster_path, 
              out_dir,  popAreaMin = 1, sampleMin = 3, percent = 0.95, 
              uninhab_path = False, anc_nd = 0, pop_nd = 0):
    '''
    Prepare population density rasters given population and ancillary data 
    through intelligent dasymetric mapping. -popFeat_path: The path to the \
    census polygons with unique identifiers and a count of the population for \
    each polygon. - popCountField: The field in the population_features that \
    stores the polygon's populations.- popKeyField: The unique identifier \
    field for each polygon in population_features. -ancRaster_path: The path \
    to the land cover raster that is used for dasymetric population mapping. \
    -out_dir: The directory where all outputs will be saved. \
    -popAreaMin: The minimum number of raster cells in a source polygon for \
    it to be considered representative of a class (default = 1). -sampleMin: \
    The minimum number of source units to ensure a representative sample for \
    a land cover class (default = 3). -percent: The minimum percent of a \
    source polygon's area that an ancillary class must cover in order for the \
    source polygon to be considered representative of that class. Enter as a \
    decimal (default = 0.95). -uninhab_path: An optional shapefile containing \
    uninhabited areas. -anc_nd: The NoData value for the ancillary raster \
    (default = 0). -pop_nd: The NoData value for the population \
    raster (default = 0)   
    '''
    #Set config.json file in the script's directory to presetTable
    if __name__ == '__main__':
        presetTable = os.path.join(sys.path[0], "config.json")
    else:
        presetTable = os.path.join(sys.path[-1], "config.json")
    
    print ('population_features path: {0}'.format(popFeat_path))
    print ('population_count_field: {0}'.format(popCountField))
    print ('population_key_field: {0}'.format(popKeyField))
    print ('ancillary_raster: {0}'.format(ancRaster_path))
    print ('uninhabited_file: {0}'.format(uninhab_path))
    print ('The minimum populated area of a representative unit is ' + str(popAreaMin))
    print ('The minimum sample size is ' + str(sampleMin))
    print ('The percent is ' + str(percent))
    print ('The NoData value for the population raster is ' + str(pop_nd))
    print ('The NoData value for the ancillary raster is ' + str(anc_nd))

    #Set file names for outputs
    popRaster = os.path.join(out_dir, "PopRaster.tif")
    popWorkTable = os.path.join(out_dir, "PopTable.csv")
    dasyRaster = os.path.join(out_dir, "DasyRaster.tif")
    dasyWorkTable = os.path.join(out_dir, "DasyWorkTable.csv")
    densityRaster = os.path.join(out_dir, "DensityRaster.tif")
    
    """
    Set driver for raster creation and read in census population features and 
    ancillary raster
    """
    rast_driver = gdal.GetDriverByName('GTiff')
    ancRaster = gdal.Open(ancRaster_path)
    popFeatures = ogr.Open(popFeat_path)
    popLayer = popFeatures.GetLayer()
    
    '''
    Get GeoTransform from ancillary raster: rows, columns, 
    coordinates of upperleft corner for north up images, and projection.
    '''
    rows = ancRaster.RasterYSize
    cols = ancRaster.RasterXSize
    ulx = ancRaster.GetGeoTransform()[0]
    uly = ancRaster.GetGeoTransform()[3]
    anc_proj = ancRaster.GetProjection()
    
    """
    Create population raster from census population features using the 
    GeoTransform from the ancillary raster. Set pop_nd as the NoData value 
    for the population raster. 
    """
    print ("Creating population raster...")
    popRast = rast_driver.Create(popRaster, cols, rows, 1, 
                                gdal.GDT_Float32, options=["COMPRESS=LZW"])
    popRast.SetGeoTransform((ulx, ancRaster.GetGeoTransform()[1], 0, 
                             uly, 0, ancRaster.GetGeoTransform()[5]))
    popRast.SetProjection(anc_proj)
    popRast.GetRasterBand(1).SetNoDataValue(pop_nd)
    gdal.RasterizeLayer(popRast, [1], popLayer, 
                        options = ["ATTRIBUTE=" + popKeyField])
    popRast = None
    
    """
    Burn the NoData value from the ancillary raster into the pixels that 
    overlap uninhabited areas
    """
    if uninhab_path:
        uninhab_ds = ogr.Open(uninhab_path)
        uninhabLayer = uninhab_ds.GetLayer()
        uninhab_anc = os.path.join(out_dir, "uninhab_landcover.tif")
        uninhab_rast = rast_driver.CreateCopy(uninhab_anc, 
                                              gdal.Open(ancRaster_path), 
                                              options=['COMPRESS=LZW'])
        gdal.RasterizeLayer(uninhab_rast, [1], uninhabLayer, 
                            burn_values = [anc_nd])
        uninhab_rast = None
        uninhab_ds = None
        ancRaster = gdal.Open(uninhab_anc)
    
    print ("Creating dasymetric units...")
    #Read ancillary raster and population raster as array
    anc_arr = ancRaster.GetRasterBand(1).ReadAsArray().astype(np.uint64)
    popRast = gdal.Open(popRaster)
    pop_arr = popRast.GetRasterBand(1).ReadAsArray().astype(np.uint64)
    
    """
    Convert pixel values of ancillary raster that do not overlap with census 
    polygons to NoData.
    """
    anc_arr[pop_arr == pop_nd] = anc_nd
    
    """
    Combine the ancillary raster and the population raster using Cantor's 
    pairing function to return a unique integer value for a pair(x,y)
    """
    comb_arr = 0.5 * (pop_arr + anc_arr) * (pop_arr + anc_arr + 1) + anc_arr 
    
    """
    Write the combine array to the dasymetric raster using the GeoTransform 
    from the ancillary raster
    """
    dasyRast = rast_driver.Create(dasyRaster, cols, rows, 1, 
                            gdal.GDT_Float64, options=['COMPRESS=LZW'])
    dasyRast.SetGeoTransform((ulx, ancRaster.GetGeoTransform()[1], 0, 
                              uly, 0, ancRaster.GetGeoTransform()[5]))
    dasyRast.SetProjection(anc_proj)
    dasyRast_b1 =dasyRast.GetRasterBand(1)
    dasyRast_b1.WriteArray(comb_arr)
    
    """
    Set the NoData value for the dasymetric raster band by running the same 
    Cantor's pairing function on the NoData values from the population raster 
    and ancillary raster.
    """
    dasy_nd = 0.5 * (pop_nd + anc_nd) * (pop_nd + anc_nd + 1) + anc_nd
    dasyRast_b1.SetNoDataValue(dasy_nd)
    dasyRast = None
    
    """
    Make the population DataFrame and the dasymetric DataFrame: collect the 
    unique values and counts, rearrange the array via transpose, convert to 
    DataFrame, and rename columns.
    """
    dasy_ar_un = np.array(np.unique(comb_arr, return_counts = True)).T
    dasy_df = pd.DataFrame(dasy_ar_un, columns = ("Value", "Count"))
    
    pop_ar_un = np.array(np.unique(pop_arr, return_counts = True)).T
    pop_df = pd.DataFrame(pop_ar_un, columns = ("Value", "Count"))
    
    '''
    Inverse of Cantor's pairing to get the polygon ID and ancillary class 
    associated with each dasy unit.
    w = (sqrt(8 * dasy_df['Value'] + 1) - 1) // 2
    '''
    num = 8*dasy_df['Value'] + 1
    dasy_df['w'] = (num.pow(1./2) - 1) // 2
    dasy_df['t'] = (dasy_df['w'].pow(2) + dasy_df['w']) / 2
    dasy_df['ancID'] = dasy_df['Value'] - dasy_df['t'] 
    dasy_df['polyID'] = dasy_df['w'] - dasy_df['ancID']

    #get rid of unnecessary columns and NoData values
    dasy_df = dasy_df[dasy_df['Value'] != dasy_nd].drop(columns = ['w','t'])
    pop_df = pop_df[pop_df['Value'] != pop_nd]

    #Set variables for DataFrame columns
    popIDField = 'polyID'
    ancCatName = 'ancID'
    dasyAreaField = 'Count'

    #Make lists to use later
    #All ancillary categories in study area
    inAncCatList = list(np.unique(dasy_df[ancCatName]).astype(int))
    
    '''            
    This list will be populated with ancillary categories that are not sampled 
    and do not have preset class densities.
    '''
    unSampledList = []
                
    #Preset class densities from config.json file
    presetData = json.load(open(presetTable))
    
    '''
    Uninhabited classes: ancially classes where people do not live. Classes with
    a preset class density of 0
    '''
    unInhabList = [int(presetCat) for presetCat,presetVal in presetData.items()
                    if float(presetVal) == 0]
    
    #Ancillary classes where people can live
    InhabList = [cat for cat in inAncCatList if cat not in unInhabList]
    
    '''
    Join the census population counts to the dasymetric DataFrame and calculate 
    population density for the polygon. 
    '''
    print ("Calculating populated area...")
    #Read the source population shapefile with the population count field.
    popfeat_df = gp.read_file(popFeat_path)

    '''
    Set the polygon ID field provided by the user as an index for the 
    population features DataFrame and the population DataFrame for joining and 
    transfering the population count field.
    '''
    popfeat_df.index = popfeat_df[popKeyField]
    pop_df.index = pop_df["Value"]
    
    '''
    Join population counts from popfeat_df to the dasymetric DataFrame and the 
    population DataFrame. Rename the field to "POP_COUNT" in the dasymetric 
    DataFrame.
    '''
    dasy_df = dasy_df.join(popfeat_df[popCountField], 
                           on = popIDField).rename(
                                   columns = {popCountField: "POP_COUNT"}
                                   )
    pop_df = pop_df.join(popfeat_df[popCountField])

    '''
    Group the dasymetric units that are associated with inhabitable classes by 
    the census polygon ID and take the sum of the dasymetric area in each 
    group. Rename the column as "POP_AREA".
    POP_AREA = sum(pixels) for inhabitable classes
    '''
    popAreaSum = dasy_df[
            dasy_df[ancCatName].isin(InhabList)
            ].groupby(popIDField)[dasyAreaField].sum().rename("POP_AREA")

    '''
    Transfer "POP_AREA" from popAreaSum to the dasymetric DataFrame and the 
    population DataFrame.
    '''      
    dasy_df["POP_AREA"] = dasy_df.join(popAreaSum, on = popIDField)["POP_AREA"]
    pop_df = pop_df.join(popAreaSum).fillna(0)

    '''
    Calculate population density for census polygons where poulated area is 
    greater than 0.
    '''
    print ("Calculating population density...")           
    pop_densMask = pop_df["POP_AREA"] > 0
    pop_df.loc[pop_densMask, "POP_DENS"] = pop_df.loc[
            pop_densMask, popCountField] / pop_df.loc[pop_densMask, "POP_AREA"]
    #replace NaN with 0
    pop_df = pop_df.fillna(0)
    
    '''
    Calculate representative population density for ancillary classes that have 
    enough representative samples in the study area.
    '''
    print ("Selecting representative units...")
    #Create column for the ancillary class that a polygon is representative of 
    pop_df["REP_CAT"] = 0

    '''
    For each inhabitable ancillary class, collect polygon IDs of census 
    polygons that meet the user-define criteria for being representative of an 
    ancillary class.
    '''        
    for inAncCat in InhabList:
        repUnits_mask = (
                dasy_df["POP_AREA"] > float(popAreaMin)
                ) & (
                        dasy_df[ancCatName] == inAncCat
                        )
        repUnits = dasy_df.loc[
                repUnits_mask, [
                        dasyAreaField, popIDField, ancCatName, "POP_AREA"
                        ]
                ]
        repUnits["PERCENT"] = repUnits[dasyAreaField] / repUnits["POP_AREA"]                
        repUnits = list(
                repUnits[repUnits["PERCENT"] >= float(percent)][popIDField]
                )
                
        if len(repUnits) >= float(sampleMin):
            pop_df.loc[pop_df['Value'].isin(repUnits), "REP_CAT"] = inAncCat
            print ("Class " 
                   + str(inAncCat) 
                   + " was sufficiently sampled with " 
                   + str(len(repUnits)) 
                   + " representative source units.")
            
            '''
            #If ancillary category has no representative polygons and it does 
            not have a preset class density, then add it to the list of 
            unsampled classes.
            '''
        elif str(inAncCat) not in list(presetData):
            unSampledList.append(int(inAncCat))
            print ("Class " 
                   + str(inAncCat) 
                   + " was not sufficiently sampled with only " 
                   + str(len(repUnits)) 
                   + " representative source units.")
            
    #Calculate statistics and make sampling summary table
    print (
            "Calculating representative population density for selected" \
            " classes..."
            )
    
    '''
    Create a mask for rows in the dasymetric DataFrame where REP_CAT =! 0. 
    We only want to create summaries for these dasymetric rows because they are 
    associated with representative polygons.
    '''
    rep_mask = pop_df["REP_CAT"] != 0

    '''
    Calculate sum of census population counts and sum of populated area for 
    each sampled ancillary class.
    '''
    classDens_df = pop_df[rep_mask].groupby("REP_CAT")[
            [popCountField, 'POP_AREA']
            ].sum().rename(
            columns = {popCountField: "SUM_" + popCountField, 
                       "POP_AREA": "SUM_POP_AREA"}
            )
            
    #Calculate sample density for sampled classes
    classDens_df["SAMPLEDENS"] = classDens_df[
            "SUM_" + popCountField
            ] / classDens_df["SUM_POP_AREA"]
    classDens_df["METHOD"] = "Sampled"
    classDens_df["CLASSDENS"] = classDens_df["SAMPLEDENS"]
                    
    #Add preset densities to summary table
    if presetTable:
        print ("Adding preset values to the summary table...")
        for preset_cat in list(presetData):
            classDens_df.loc[int(preset_cat), "CLASSDENS"] = presetData[
                    preset_cat
                    ]
            classDens_df.loc[int(preset_cat), "METHOD"] = 'Preset'
            
    # For all sampled and preset classes, calculate a population estimate.
    print (
            "Calculating population estimate for sampled and preset classes..."
            )            
    #Get representative population densities from class density DataFrame.
    dasy_df = dasy_df.join(classDens_df['CLASSDENS'], on = ancCatName).fillna(0)
    
    '''
    #Set mask for dasy_df that will limit ancillary categories to those in the 
    class density DataFrame.
    '''
    popEst_mask = dasy_df[ancCatName].isin(classDens_df.index)
    
    '''
    POP_EST = area of the dasymetric unit 
    * the representative population density of the ancillary class associated 
    with the dasymetric unit
    '''
    dasy_df["POP_EST"] = 0
    dasy_df.loc[popEst_mask, "POP_EST"] = dasy_df.loc[
            popEst_mask, dasyAreaField
            ] * dasy_df.loc[
                    popEst_mask, 'CLASSDENS'
                    ]
    
    # Intelligent areal weighting for unsampled classes            
    print ("Performing intelligent areal weighting for unsampled classes...")
    if unSampledList:
        '''
        Calculate representative population densities for unsampled ancillary 
        classes using IAW
        '''
        unsampled_mask = dasy_df[ancCatName].isin(unSampledList)
        
        '''
        Populate remainining area of each dasymetric unit as the area of 
        dasymetric units associated with unsampled classes and 0 everywhere 
        else.
        '''
        dasy_df["REM_AREA"] = 0
        dasy_df.loc[unsampled_mask, "REM_AREA"] = dasy_df.loc[
                unsampled_mask, dasyAreaField
                ]
        
        '''                          
        For each polygon, sum the remaining area and sum the population that 
        has already been estimated for sampled/preset classes.
        '''
        popEstSum = dasy_df.groupby(popIDField)[
                ["POP_EST", "REM_AREA"]
                ].sum()
        
        '''
        Join popEstSum to dasy_df to transfer the sum of population estimates 
        and the sum of remaining area to the dasymetric DataFrame.
        '''
        dasy_df = dasy_df.join(popEstSum["POP_EST"], on = popIDField, 
                               rsuffix = "poly")
        dasy_df = dasy_df.join(popEstSum["REM_AREA"], on = popIDField, 
                               rsuffix = "poly")
        
        '''
        Calcualte a population difference between the census population and the 
        population estimated for sampled/preset ancillary classes.
        '''
        dasy_df["POP_DIFF"] = dasy_df["POP_COUNT"] - dasy_df["POP_ESTpoly"]
        
        '''
        Calculate an initial population estimate for dasymetric units 
        associated with unsampled ancillary classes and polygons where the 
        sampled/preset population estimates did not exceed the census 
        population count. 
        '''
        diff_mask = (dasy_df[ancCatName].isin(unSampledList) &
                     dasy_df['REM_AREApoly'] !=0 )
        dasy_df.loc[diff_mask, "POP_EST"] = (
                dasy_df.loc[diff_mask, "POP_DIFF"].clip(0) * 
                dasy_df.loc[diff_mask, "REM_AREA"] / 
                dasy_df.loc[diff_mask, "REM_AREApoly"])
        '''
        Sum total initial population estimates and remaining area for 
        dasymetric units used to calculate initial population estimates for 
        unsampled ancillary classes.
        '''
        ancCat_sum = dasy_df[diff_mask].groupby(ancCatName)[
                ["POP_EST" , "REM_AREA"]
                ].sum()
        
        '''
        Calculate the representative population density for unsampled classes 
        using ancCat_sum and update the class density DataFrame.
        '''
        for cat in ancCat_sum.index:
            classDens_df.loc[cat, "CLASSDENS"] = ancCat_sum.loc[cat, 
                            "POP_EST"] / ancCat_sum.loc[cat, 
                                           "REM_AREA"]
            classDens_df.loc[cat, "METHOD"] = "IAW"   
        
        '''
        Add representative population densities for unsampled classes in the 
        dasymetric DataFrame.
        '''
        dasy_df.loc[unsampled_mask, 'CLASSDENS'] = dasy_df.loc[
                unsampled_mask
                ].join(classDens_df.loc[
                        ancCat_sum.index, 'CLASSDENS'
                        ], 
                on = ancCatName, rsuffix = "_classDens")['CLASSDENS_classDens']
        
        '''
        Calculate new population estimates using representative population 
        densities for unsampled classes.
        POP_EST = dasymetric area * class density
        '''
        dasy_df.loc[unsampled_mask, "POP_EST"] = dasy_df.loc[unsampled_mask, 
                   dasyAreaField] * dasy_df.loc[unsampled_mask, 
                               'CLASSDENS']
                               
        # End of intelligent areal weighting
             
    # Perform final calculations to ensure pycnophylactic integrity
    print (
            "Performing final calculations to ensure pycnophylactic" \
            " integrity..."
            )
    '''
    For each dasymetric unit, use the ratio of the estimated population to the 
    total population estimated for the polygon associated with the dasymetric 
    unit to redistribute the census population.
    '''

    '''
    if the sum of population densities within the source unit is equal to 0
    set the POP_EST for those to 1 (i.e., area weighting (equation 5))
    '''

    idx = (dasy_df
            .groupby(popIDField)
            .filter(
                lambda s: s['POP_EST'].sum() == 0 and
                          s['POP_COUNT'].sum() > 0
                    ).index
            )

    dasy_df.loc[idx, 'POP_EST'] = 1
    
    #Sum population estimates by polygon.
    popEstsum = dasy_df.groupby(popIDField)["POP_EST"].sum()
    
    dasy_df["TOTALFRACT"] = dasy_df["POP_EST"] / dasy_df.join(popEstsum, 
           on = popIDField, rsuffix = "SUM")["POP_ESTSUM"]
    dasy_df["NEW_POP"] = dasy_df["TOTALFRACT"] * dasy_df["POP_COUNT"]
    dasy_df["NEWDENSITY"] = dasy_df["NEW_POP"] / dasy_df[dasyAreaField]
    
    #Replace nan with 0
    dasy_df = dasy_df.fillna(0)
    
    #export dasy table to .csv
    dasy_df.to_csv(dasyWorkTable, header = True)
               
    #export pop_df to .csv
    pop_df.fillna(0).to_csv(popWorkTable, header = True)
            
    #export classDens_df to sampling summary table
    classDens_df.to_csv(os.path.join(out_dir, "SamplingSummaryTable.csv"), 
                        header = True)
    
    #Create final population density raster.
    print ("Creating population density raster...")
    #Create population density array.
    dasy_lut = dasy_df[['Value', 'NEWDENSITY']].set_index('Value')
    dasy_lut.loc[dasy_nd, 'NEWDENSITY'] = -999 #NoData value from comb_arr
    dens_df = pd.DataFrame(np.ravel(comb_arr)).join(dasy_lut, on = 0)
    dens_ar = np.array(
            dens_df['NEWDENSITY']
            ).reshape(
                    (comb_arr.shape[0], comb_arr.shape[1])
                    )
    
    #Write array to population density raster.
    densRast = rast_driver.Create(densityRaster, cols, rows, 1, 
                                  gdal.GDT_Float32, options=['COMPRESS=LZW'])
    densRast.SetGeoTransform((ulx, ancRaster.GetGeoTransform()[1], 0, 
                              uly, 0, ancRaster.GetGeoTransform()[5]))
    densRast.SetProjection(anc_proj)
    densRast_b1 =densRast.GetRasterBand(1)
    densRast_b1.WriteArray(dens_ar)
    densRast_b1.SetNoDataValue(-999)
    densRast = None
    
    print ("All outputs from this tool can be found in " + out_dir)

#------------------------------------------------------------------------------
#Get arguments to run dasy_pop from command line
if __name__ == '__main__':
    #create ArgumentParser
    parser = ap.ArgumentParser(description='This script accepts population \
                               and ancillary datasets for preparing \
                               population density rasters using intelligent \
                               dasymetric mapping.')
    
    #add arguments
    parser.add_argument('population_features', type = str, 
                        help = 'The census polygons with unique identifiers \
                        and a count of the population for each polygon')
    parser.add_argument('population_count_field', type = str, 
                        help = "The field in the population_features that \
                        stores the polygon's populations")
    parser.add_argument('population_key_field', type = str, 
                        help = "The unique identifier field for each polygon \
                        in population_features")
    parser.add_argument('ancillary_raster', type = str, 
                        help = "The land cover raster that is used for \
                        dasymetric population mapping")
    parser.add_argument('output_directory', type = str, 
                        help = "The directory where all outputs from the \
                        script will be saved.")
    parser.add_argument('--uninhabited_file', type = str, nargs='?', 
                        help = "An optional feature class containing \
                        uninhabited areas")
    parser.add_argument('--minimum_sampling_area', type = int, 
                        nargs='?',default = 1, 
                        help = "The minimum number of raster cells in a \
                        source polygon for it to be considered representative \
                        of a class - default = 1")
    parser.add_argument('--minimum_sample', type = int, nargs='?', default = 3, 
                        help = "The minimum number of source units to ensure \
                        a representative sample for a land cover class \
                        - default = 3")
    parser.add_argument('--percent', type = float, nargs='?', default = 0.95, 
                        help = "The minimum percent of a source polygon's \
                        area that an ancillary class must cover in order for \
                        the source polygon to be considered representative of \
                        that class. Please enter as a decimal \
                        - default = 0.95")
    parser.add_argument('--pop_nodata', type = int, nargs='?', default = 0, 
                        help = "The population_features will be converted to \
                        raster and this will be the NoData value \
                        - default = 0")
    parser.add_argument('--anc_nodata', type = int, nargs='?', default = 0, 
                        help = "The NoData value for the ancillary raster \
                        - default = 0")   

    #get args
    args = parser.parse_args()
        
    #run function
    dasy_map(
            popFeat_path = args.population_features, 
            popCountField = args.population_count_field, 
            popKeyField = args.population_key_field, 
            ancRaster_path = args.ancillary_raster, 
            popAreaMin = args.minimum_sampling_area, 
            sampleMin = args.minimum_sample,
            percent = args.percent, 
            uninhab_path = args.uninhabited_file,
            out_dir = args.output_directory,
            anc_nd = args.pop_nodata,
            pop_nd = args.anc_nodata
            )
