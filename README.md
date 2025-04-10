# README

Last updated by [Yiyuan Lin](yl3663@cornell.edu) on Apr 10, 2025



# Vineyard Image-to-Vine Matching Pipeline

This pipeline processes vineyard images and GPS data collected by autonomous systems. It projects image fields-of-view (FOV) onto vineyard rows, determines which grapevines are covered in each image, and provides various visualization tools for debugging and verification.



## Directory Structure

```bash
project_root/
├── Data
│   └── OBlock
│       ├── Grapevines_Geo_Reference.csv   # Grapevine root positions with row and ID 
│       ├── Image_GPS.csv                  # Raw image GPS logs 
│       ├── Row_SE_GPS_OBlock.csv          # Grapevine root positions with row and ID 
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



## Running the Pipeline

Ensure your terminal is in the project root and required packages are installed (`pandas`, `numpy`, `matplotlib`):

```bash
python main_pipeline.py [options]
```





## Processing Steps

| Step | Description                                                  |
| ---- | ------------------------------------------------------------ |
| 0    | Compute grapevine coverage span along rows                   |
| 1    | Classify image direction as F (forward) or B (backward)      |
| 2    | Compute camera position offset from GPS (e.g. 0.76m to the left) |
| 3    | Assign each camera point to its nearest row                  |
| 4    | Compute FOV intersections (center/left/right) on the row     |
| 5    | Match image FOV to overlapping grapevine coverage spans      |
| 6    | Save results to `Image_GPS_FOV_matched_vines.csv`            |
| 7    | Optional: visualize any of the above                         |



## Input Files

| File                           | Description                                                  |
| ------------------------------ | ------------------------------------------------------------ |
| `Image_GPS.csv`                | Must include: `Image_ID`, `Latitude`, `Longitude`            |
| `Row_SE_GPS_OBlock.csv`        | Two entries per row (S and E), columns: `Row`, `ID`, `Longitude`, `Latitude` |
| `Grapevines_Geo_Reference.csv` | Columns: `Row`, `ID`, `Longitude`, `Latitude`                |



## Command-Line Options

| Argument                 | Description                                                  |
| ------------------------ | ------------------------------------------------------------ |
| `--check_raw_data`       | Visualize raw grapevine, GPS, and row layout                 |
| `--check_direction`      | Visualize image GPS points by movement direction (F/B)       |
| `--check_camera`         | Visualize projected camera positions and row vectors         |
| `--check_assigned_row`   | Visualize camera points colored by their assigned row        |
| `--fov_samples N`        | Randomly visualize `N` FOV projections intersecting vineyard rows |
| `--visualize_vine_cam N` | Visualize `N` image FOVs and which grapevines they cover     |



## Examples

- Run full pipeline with visualization:

```bash
python main_pipeline.py --check_raw_data --check_direction --check_camera --check_assigned_row --fov_samples 5 --visualize_vine_cam 5
```

- Run silently to generate output CSV:

```bash
python main_pipeline.py
```

- Visualize 3 images and the grapevines they cover:

```bash
python main_pipeline.py --visualize_vine_cam 3
```



## Output Files

| File                              | Description                                                  |
| --------------------------------- | ------------------------------------------------------------ |
| `Grapevines_with_Coverage.csv`    | Each vine’s projected coverage range along the row           |
| `Image_GPS_FOV_matched_vines.csv` | Image-to-vine matches with FOV geometry and `Covered_Vines` column |



## Notes

- Assumes `Image_ID` increases in acquisition order (e.g. frame sequence).
- Camera is assumed to be mounted on the **left side** of GPS unit.
- All projection and matching computations are done in **local meter space**, using GPS as a reference frame.
