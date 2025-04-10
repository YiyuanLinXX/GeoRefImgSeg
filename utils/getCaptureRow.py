import pandas as pd
import numpy as np

def point_to_line_distance_degree(P, P0, d):
    """
    Compute perpendicular distance from point P to infinite line defined by P0 and direction d,
    all in degree units.
    """
    v = P - P0
    s = np.dot(v, d)
    foot = P0 + s * d
    return np.linalg.norm(P - foot)

def assign_image_rows(df_with_camera, row_file):
    """
    Assigns each image (camera) point to the nearest row line based on Camera_Long and Camera_Lat.
    
    Parameters:
        df_with_camera: DataFrame containing ['Camera_Long', 'Camera_Lat'] for each image
        row_file: path to vineyard row start/end file

    Returns:
        df: original DataFrame with new column 'Assigned_Row'
    """
    df = df_with_camera.copy()
    cam_pts = np.vstack([df["Camera_Long"], df["Camera_Lat"]]).T

    df_row = pd.read_csv(row_file)
    row_lines = []
    for row_val in df_row['Row'].unique():
        sub = df_row[df_row['Row'] == row_val]
        S = sub[sub['ID'] == 'S'].iloc[0]
        E = sub[sub['ID'] == 'E'].iloc[0]
        P0 = np.array([S["Longitude"], S["Latitude"]])
        d_raw = np.array([E["Longitude"] - S["Longitude"], E["Latitude"] - S["Latitude"]])
        norm = np.linalg.norm(d_raw)
        d = d_raw / norm if norm > 1e-6 else np.array([1.0, 0.0])
        row_lines.append((row_val, P0, d))

    assigned = []
    for P in cam_pts:
        best_row = -1
        best_dist = float('inf')
        for row_val, P0, d in row_lines:
            dist = point_to_line_distance_degree(P, P0, d)
            if dist < best_dist:
                best_dist = dist
                best_row = row_val
        assigned.append(best_row)

    df["Assigned_Row"] = assigned
    return df
