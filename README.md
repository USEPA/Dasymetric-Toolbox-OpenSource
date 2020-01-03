
# Intelligent Dasymetric Toolbox (Open Source)

[<img src="https://enviroatlas.epa.gov/enviroatlas/interactivemap/images/logo.png"     title="EnviroAtlas" width=400 >](https://www.epa.gov/enviroatlas)

## Overview
Dasymetric mapping is a geospatial technique that uses information such as land cover types to more accurately distribute data within selected boundaries like census blocks.

The Intelligent Dasymetric Mapping (IDM) Toolbox is available to download. This toolbox uses Python 3.6 and open source GIS libraries. An additional version is available as a [toolbox for ESRI ArcGIS Pro](https://github.com/USEPA/Dasymetric-Toolbox-ArcGISPro)


<figure>
  <img src="https://www.epa.gov/sites/production/files/styles/large/public/2015-07/dasymetric_728x210.jpg" alt="my alt text"/>
  <figcaption><sup>The image on the left shows a map of the population by block group based solely on the census data. The image on the right shows the dasymetric population allocation for several block groups in Tampa, Fla.</sup></figcaption>
</figure>
<br>


-   EnviroAtlas researchers use the dasymetric data to calculate the distribution of ecosystem services, and other metrics including walking distances, viewsheds, resource use, and exposure potential.
-   For more information on the Dasymetric data created for EnviroAtlas, see our [website](https://www.epa.gov/enviroatlas/dasymetric-toolbox) or  [Dasymetric Allocation of Population Fact Sheet](https://enviroatlas.epa.gov/enviroatlas/DataFactSheets/pdf/Supplemental/DasymetricAllocationofPopulation.pdf).


## Installation
To install this application you will need Python 3.6 and several libraries. A [conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/download.html) environment file is provided.
```bash
# Clone this repository
$ git clone https://github.com/USEPA/Dasymetric-Toolbox-OpenSource

# Go into the repository
$ cd Dasymetric-Toolbox-OpenSource

# create environment
$ conda env create -f environment.yml

# Activate environment
$ source activate idm 
# for Windows use [conda activate idm]

# Run the app
$ python idm.py --help
```

## Usage
```
idm.py [-h] [uninhabited_file] [minimum_sampling_area] [minimum_sample] 
[percent] [pop_nodata] [anc_nodata] population_features 
population_count_field population_key_field ancillary_raster output_directory 
```
### Description
-h, --help  
Description and explanation of arguments

uninhabited_file (optional)
An optional feature class containing uninhabited areas

minimum_sampling_area
The minimum number of raster cells in a source polygon for it to be considered representative 
of a class - default = 1

minimum_sample
The minimum number of source units to ensure a representative sample for a land cover class - default = 3

percent
The minimum percent of a source polygon's area that an ancillary class must cover in order for 
the source polygon to be considered representative of that class. Please enter as a decimal - default = 0.95

pop_nodata
The population_features will be converted to raster and this will be the NoData value - default = 0

anc_nodata  
The NoData value for the ancillary raster - default = 0

population_features  
Path to polygon shapefile with unique identifiers and a count of the population for each polygon

population_count_field  
The field in the population_features that stores the polygon's populations

population_key_field  
The unique identifier field (must be positive whole numbers) for each polygon in population_features.  

ancillary_raster  
Path to categorical raster (e.g., GeoTiff) containing classes that are indicative of the spatial distribution of population (e.g., land cover). 

output_directory  
Path where all outputs from the script will be saved.

### Preset Densities
The user can set a population density for any ancillary class using their own domain knowledge by modifying the 'config.json' file in the toolbox's root directory. 

The preset densities for the following land cover classes from the 2011 National Land Cover Database (NLCD) are set to 0 people per pixel:

* 11, Open Water
* 12, Perennial Ice/Snow
* 95, Emergent Herbaceous Wetlands


### Examples
[Example data](data) are provided.
```bash
mkdir -p output
python idm.py ./data/2010_blocks_DE.shp POP10 polyID ./data/nlcd_2011_DE.tif ./output
```
Running the script with uninhabited polygons
```bash
mkdir -p output
python idm.py --uninhabited_file uninhab_DE.shp ./data/2010_blocks_DE.shp POP10 polyID ./data/nlcd_2011_DE.tif ./output
```
## Contact

U.S. Environmental Protection Agency  
Office of Research and Development  
Durham, NC 27709  
[https://www.epa.gov/enviroatlas/forms/contact-us-about-enviroatlas](https://www.epa.gov/enviroatlas/forms/contact-us-about-enviroatlas)



## Credits
The Intelligent Dasymetric Toolbox for ArcGIS Pro was developed for [EnviroAtlas](https://www.epa.gov/enviroatlas). EnviroAtlas is a collaborative effort led by U.S. EPA that provides geospatial data, easy-to-use tools, and other resources related to ecosystem services, their stressors, and human health. 

The dasymetric  toolbox was updated for ArcGIS Pro in January 2020 by **Anam Khan**<sup>1</sup> and **Jeremy Baynes**<sup>2</sup>. This release also introduced optional functionality to mask known uninhabited areas.

The toolbox was originally developed for ArcMap 10 by **Torrin Hultgren**<sup>3</sup> 

The dasymetric toolbox follows the the methods by **Mennis and Hultgren (2006)**<sup>4</sup>. 

<sub><sup>1</sup> Oak Ridge Associated Universities, National Student Services Contractor at the U.S. EPA</sub>
<sub><sup>2</sup> U.S. EPA</sub>
<sub><sup>3</sup> National Geospatial Support Team at U.S. EPA</sub>
<sub><sup>4</sup> Mennis, Jeremy & Hultgren, Torrin. (2006).  Intelligent Dasymetric Mapping and Its Application to Areal Interpolation. Cartography and Geographic Information Science. 33. 179-194.</sub>


## License
MIT License

Copyright (c) 2019 U.S. Federal Government (in countries where recognized)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## EPA Disclaimer
*The United States Environmental Protection Agency (EPA) GitHub project code is provided on an "as is" basis and the user assumes responsibility for its use.  EPA has relinquished control of the information and no longer has responsibility to protect the integrity , confidentiality, or availability of the information.  Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by EPA.  The EPA seal and logo shall not be used in any manner to imply endorsement of any commercial product or activity by EPA or the United States Government.*