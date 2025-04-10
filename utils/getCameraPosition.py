import pandas as pd
import numpy as np
import math

def compute_camera_positions(gps_file, offset_m=0.76):
    """
    Computes the approximate camera positions offset to the left of
    the robot's moving direction, in geographic degree space.

    Parameters:
        gps_file: path to Image_GPS.csv containing ['Image_ID', 'Latitude', 'Longitude']
        offset_m: distance to shift camera position leftward (in meters)

    Returns:
        df: a DataFrame with additional columns ['Camera_Long', 'Camera_Lat']
    """
    df = pd.read_csv(gps_file)
    df = df.sort_values(by="Image_ID").reset_index(drop=True)

    n = len(df)
    if n == 0:
        raise ValueError("Image_GPS.csv contains no data.")

    camera_lats = []
    camera_lons = []

    last_vec_m = np.array([1.0, 0.0])  # fallback direction in meters

    for i in range(n):
        lat_i = df.at[i, "Latitude"]
        lon_i = df.at[i, "Longitude"]

        lat_factor = 111320.0
        lon_factor = 111320.0 * math.cos(math.radians(lat_i))

        # Determine movement vector
        if i < n-1 and int(df.at[i+1, "Image_ID"]) - int(df.at[i, "Image_ID"]) == 1:
            lat_j = df.at[i+1, "Latitude"]
            lon_j = df.at[i+1, "Longitude"]
            dx_m = (lon_j - lon_i) * lon_factor
            dy_m = (lat_j - lat_i) * lat_factor
            dist = math.hypot(dx_m, dy_m)
            if dist > 1e-6:
                move_vec_m = np.array([dx_m/dist, dy_m/dist])
                last_vec_m = move_vec_m
            else:
                move_vec_m = last_vec_m
        else:
            move_vec_m = last_vec_m

        # Left direction (rotated +90 degrees)
        left_m = np.array([-move_vec_m[1], move_vec_m[0]])

        cam_x_m = offset_m * left_m[0]
        cam_y_m = offset_m * left_m[1]

        delta_lon = cam_x_m / lon_factor
        delta_lat = cam_y_m / lat_factor

        cam_lon = lon_i + delta_lon
        cam_lat = lat_i + delta_lat

        camera_lons.append(cam_lon)
        camera_lats.append(cam_lat)

    df["Camera_Long"] = camera_lons
    df["Camera_Lat"] = camera_lats
    return df