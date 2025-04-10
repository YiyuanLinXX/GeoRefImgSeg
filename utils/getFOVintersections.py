import pandas as pd
import numpy as np
import math


def compute_fov_intersections(df, row_file, fov_deg=60.5):
    """
    For each row in df (must include Camera_Long, Camera_Lat, Image_ID, Assigned_Row),
    compute:
        - FOV center direction vector based on movement
        - FOV boundary vectors (±fov_deg/2)
        - Intersection points with the assigned row (center, left, right)
    Returns the same df with new columns:
        - FOV_Center_Long, FOV_Center_Lat
        - FOV_Left_Long,   FOV_Left_Lat
        - FOV_Right_Long,  FOV_Right_Lat
    """

    def rotate_vector(vec, angle_deg):
        theta = math.radians(angle_deg)
        c, s = math.cos(theta), math.sin(theta)
        return np.array([c * vec[0] - s * vec[1], s * vec[0] + c * vec[1]])

    def ray_line_intersection_degree(R0, Rd, P0, d):
        denom = Rd[0] * d[1] - Rd[1] * d[0]
        if abs(denom) < 1e-9:
            return None
        diff = P0 - R0
        t = (diff[0]*d[1] - diff[1]*d[0]) / denom
        if t < 0:
            return None
        return R0 + t * Rd

    # Load rows
    df_row = pd.read_csv(row_file)
    row_dict = {}
    for row_val in df_row['Row'].unique():
        sub = df_row[df_row['Row'] == row_val]
        S = sub[sub['ID'] == 'S'].iloc[0]
        E = sub[sub['ID'] == 'E'].iloc[0]
        P0 = np.array([S["Longitude"], S["Latitude"]])
        d_raw = np.array([E["Longitude"] - S["Longitude"], E["Latitude"] - S["Latitude"]])
        d = d_raw / np.linalg.norm(d_raw) if np.linalg.norm(d_raw) > 1e-9 else np.array([1.0, 0.0])
        row_dict[row_val] = (P0, d)

    n = len(df)
    half_angle = fov_deg / 2.0
    cam_coords = df[["Camera_Long", "Camera_Lat"]].values

    centers = []
    lefts = []
    rights = []

    for i in range(n):
        cam = cam_coords[i]
        row_val = df.at[i, "Assigned_Row"]
        if row_val not in row_dict:
            centers.append([np.nan, np.nan])
            lefts.append([np.nan, np.nan])
            rights.append([np.nan, np.nan])
            continue

        # motion vector
        if i < n - 1 and int(df.at[i + 1, "Image_ID"]) - int(df.at[i, "Image_ID"]) == 1:
            next_pt = cam_coords[i + 1]
            move_vec = next_pt - cam
        elif i > 0:
            prev_pt = cam_coords[i - 1]
            move_vec = cam - prev_pt
        else:
            move_vec = np.array([1e-6, 0])
        move_unit = move_vec / np.linalg.norm(move_vec) if np.linalg.norm(move_vec) > 1e-9 else np.array([1.0, 0.0])
        v_cam = np.array([-move_unit[1], move_unit[0]])

        # FOV boundaries
        v1 = rotate_vector(v_cam, +half_angle)
        v2 = rotate_vector(v_cam, -half_angle)

        # intersection with assigned row
        P0, d_row = row_dict[row_val]
        I_center = ray_line_intersection_degree(cam, v_cam, P0, d_row)
        I1 = ray_line_intersection_degree(cam, v1, P0, d_row)
        I2 = ray_line_intersection_degree(cam, v2, P0, d_row)

        centers.append(I_center if I_center is not None else [np.nan, np.nan])
        lefts.append(I1 if I1 is not None else [np.nan, np.nan])
        rights.append(I2 if I2 is not None else [np.nan, np.nan])

    df["FOV_Center_Long"], df["FOV_Center_Lat"] = zip(*centers)
    df["FOV_Left_Long"], df["FOV_Left_Lat"]     = zip(*lefts)
    df["FOV_Right_Long"], df["FOV_Right_Lat"]   = zip(*rights)

    return df
