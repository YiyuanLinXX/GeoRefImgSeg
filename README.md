# GeoRefImgSeg: Geo-reference Based Image Segregation

Last updated by [Yiyuan Lin](yl3663@cornell.edu) on Apr 10, 2025

---



This repository provides a complete Python pipeline for processing geo-referenced vineyard GPS data and image data collected by our autonomous phenotyping robot [PPBv2](https://yiyuanlinxx.github.io/portfolio/2_PPB_V2/) at [CAIR Lab](https://cair.cals.cornell.edu/). It matches image GPS positions with vineyard rows and grapevines, computes camera view geometry, and identifies which vines are covered in each image. Optional visualizations assist in inspection and validation at every step.

Specifically, we measured the GPS coordinates at the base (root) of each grapevine in the vineyard and projected all of them onto a single straight line to simplify the processing workflow. This simplification proved to be both reasonable and effective. We refer to these processed coordinates as geo-reference data.

As our robot autonomously navigates through the vineyard to collect data, both image data and synchronized GPS coordinates of the robot are recorded. By combining these data with the geo-reference data, we determine which grapevine canopies are included in each captured image.



## Directory Structure

```bash
project_root/
├── autoProjection.py
├── Data
│   └── OBlock                             # Data files template
│       ├── Grapevines_Geo_Reference.csv   # Grapevine root positions with row and ID 
│       ├── Image_GPS.csv                  # Raw image GPS logs 
│       ├── Row_SE_GPS_OBlock.csv          # Grapevine rows starting and ending points positions with row and ID 
│       ├── (output_data)
├── main_pipeline.py
└── utils
    ├── getCameraPosition.py
    ├── getCaptureRow.py
    ├── getFOVintersections.py
    ├── getMovingDirection.py
    ├── getVineCoverage.py
    ├── __init__.py
    ├── matchVinesInCamFOV.py
    ├── plotData.py

```



## Prerequisite

- Install necessary python packages by running the following command in the terminal

  - if you are using `conda`, run

    ```bash
    conda create -n GeoRefImgSeg python=3.9 -y
    conda activate GeoRefImgSeg
    pip install -r requirements.txt
    ```


  - if you are using python virtual environment, run

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

  - if you are not using any virtual environment, then run

    ```bash
    pip install -r requirements.txt
    ```

    


## Quick Start in 1 min

1. Run the main pipeline with provided template data files

   ```bash
   python main_pipeline.py # use python3 if package python-is-python3 is not installed
   # python3 main_pipiline.py
   ```

2. Check the output results in `Data/OBlock/`.



## Usage

0. Prepared the files and project the GPS coordinates of the grapevines onto the row.

   ```bash
   python3 autoProjection.py \
       --row_se_file_path /path/to/Row_SE_GPS.csv \
       --grapevine_file_path /path/to/Grapevines_GPS_origin.csv \
       --output_file_path /path/to/Grapevines_Geo_Reference.csv
   ```

1. Place your input CSV files in `Data/{Your_Dataset}/` following the provided formats in `Data/OBlock`.

   - `Grapevines_Geo_Reference.csv`: includes the projected GPS coordinates of the grapevines

     ```csv
     Row,ID,Longitude,Latitude
     9,1,-77.01115315,42.89455916
     9,2,-77.01115282,42.89454384
     9,3,-77.01115245,42.89452714
     9,4,-77.01115207,42.89450972
     9,5,-77.01115176,42.89449545
     ......
     ```

   - `Row_SE_GPS_OBlock.csv`: includes the gps coordinates of the starting and ending points of the rows of the grapevines

     ```csv
     Row,ID,Longitude,Latitude
     9,S,-77.01115364,42.89458162
     9,E,-77.01112139,42.89310474
     10,S,-77.01111706,42.89458164
     10,E,-77.01108579,42.89310452
     11,S,-77.01107858,42.89458073
     11,E,-77.011047,42.89310143
     ...
     ```

   - `Image_GPS.csv`: includes the image ID, GPS coordinates data (columns `Computer_Time`, `ROS_Time_Stamp`, `Chunk_Frame_ID`, `Chunk_Time` are not used in this image segregation pipeline)

     ```csv
     Image_ID,Computer_Time,ROS_Time_Stamp,Chunk_Frame_ID,Chunk_Time,Latitude,Longitude
     29,2024-09-20-14-40-22-175,1726857622,140,5.08E+11,42.89456602,-77.01116628
     30,2024-09-20-14-40-22-697,1726857623,141,5.09E+11,42.8945619,-77.0111663
     31,2024-09-20-14-40-23-220,1726857623,142,5.09E+11,42.89455927,-77.01116659
     32,2024-09-20-14-40-23-742,1726857624,143,5.10E+11,42.89455492,-77.01116659
     33,2024-09-20-14-40-24-265,1726857624,144,5.10E+11,42.89455184,-77.01116685
     ......
     ```

2. Run the main pipeline

   ```bash
   python3 main_pipeline.py [OPTIONS]
   ```

   

## Examples

- Run full pipeline with visualization:

```bash
python main_pipeline.py \
  --grapevines_file Data/OBlock/Grapevines_Geo_Reference.csv \
  --image_gps_file Data/OBlock/Image_GPS.csv \
  --row_file Data/OBlock/Row_SE_GPS_OBlock.csv \
  --grapevine_coverage_file_output_path Data/OBlock/Grapevines_with_Coverage.csv \
  --final_output_path Data/OBlock/Image_GPS_FOV_matched_vines.csv \
  --offset_m 0.76 \
  --cam_fov_degree 60.5 \
  --extend_first_last 0.5 \
  --extend_not_continuous 1.0 \
  --max_half_extend 1.2 \
  --check_raw_data \
  --check_direction \
  --check_camera \
  --check_assigned_row \
  --fov_samples 10 \
  --visualize_vine_cam 5
```

- Minimal pipeline run (silent, default paths):

```bash
python3 main_pipeline.py
```

- Visualize 3 images and the grapevines they cover:

```bash
python3 main_pipeline.py --visualize_vine_cam 3
```



##  Command-Line Arguments

| Argument                                | Description                                                 | Default                                       |
| --------------------------------------- | ----------------------------------------------------------- | --------------------------------------------- |
| `--grapevines_file`                     | Input CSV with grapevine locations                          | `Data/OBlock/Grapevines_Geo_Reference.csv`    |
| `--image_gps_file`                      | Input CSV with image GPS logs                               | `Data/OBlock/Image_GPS.csv`                   |
| `--row_file`                            | Input CSV with row start/end positions                      | `Data/OBlock/Row_SE_GPS_OBlock.csv`           |
| `--grapevine_coverage_file_output_path` | Where to save computed grapevine coverage                   | `Data/OBlock/Grapevines_with_Coverage.csv`    |
| `--final_output_path`                   | Output CSV with matched results                             | `Data/OBlock/Image_GPS_FOV_matched_vines.csv` |
| `--offset_m`                            | Distance (meters) from GPS receiver to camera (left offset) | `0.76`                                        |
| `--cam_fov_degree`                      | Camera horizontal field of view in degrees                  | `60.5`                                        |
| `--extend_first_last`                   | Extension (m) for first/last vine coverage                  | `0.5`                                         |
| `--extend_not_continuous`               | Extension (m) for non-continuous ID vines                   | `1.0`                                         |
| `--max_half_extend`                     | Max coverage from vine center to midpoint (m)               | `1.2`                                         |
| `--check_raw_data`                      | Visualize raw GPS, grapevine, and row data                  | `False`                                       |
| `--check_direction`                     | Visualize movement direction classification (F/B)           | `False`                                       |
| `--check_camera`                        | Visualize camera projection offset and row layout           | `False`                                       |
| `--check_assigned_row`                  | Visualize color-coded row assignments                       | `False`                                       |
| `--fov_samples N`                       | Plot `N` random images with FOV projection                  | `0`                                           |
| `--visualize_vine_cam N`                | Plot `N` random images with vine coverage matching          | `0`                                           |



## Outputs

| File                              | Description                                                  |
| --------------------------------- | ------------------------------------------------------------ |
| `Grapevines_with_Coverage.csv`    | Each vine’s projected coverage range (start/end) along the row |
| `Image_GPS_FOV_matched_vines.csv` | Image FOV projections and matched vine IDs                   |

- Visualizations (if enabled) displayed inline via `matplotlib`



## Processing Steps

1. **Compute vine canopy coverage** on vineyard row.
2. **Determine robot movement direction** using consecutive GPS points.
3. **Compute camera position** offset from GPS based on direction.
4. **Assign camera point to nearest row**.
5. **Project camera FOV** and compute intersections.
6. **Match grapevines** whose canopies intersect with FOV.
7. **Export results**, optionally visualize each step.



## Notes

- Assumes `Image_ID` increases in acquisition order (e.g. frame sequence).
- Camera is assumed to be mounted on the **left side** of GPS unit.
- All projection and matching computations are done in **local meter space**, using GPS as a reference frame.
