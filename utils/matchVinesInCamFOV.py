import pandas as pd
import numpy as np
import math

def latlon_to_meters(lat, lon, ref_lat, ref_lon):
    d_lat = lat - ref_lat
    d_lon = lon - ref_lon
    ref_lat_rad = math.radians(ref_lat)
    x = d_lon * 111320.0 * math.cos(ref_lat_rad)
    y = d_lat * 111320.0
    return x, y

def project_point_on_row(lon, lat, ref_lat, ref_lon, dx_r, dy_r, norm_d):
    px, py = latlon_to_meters(lat, lon, ref_lat, ref_lon)
    direction_unit = np.array([dx_r, dy_r]) / norm_d
    return px * direction_unit[0] + py * direction_unit[1]

def match_vines_in_fov(df_imgs, row_file, vine_file):
    df_imgs = df_imgs.copy()
    df_imgs["Covered_Vines"] = ""

    df_vines = pd.read_csv(vine_file)
    df_rows = pd.read_csv(row_file)

    row_map = {}
    for row_val in df_rows["Row"].unique():
        sub = df_rows[df_rows["Row"] == row_val]
        S = sub[sub["ID"] == "S"].iloc[0]
        E = sub[sub["ID"] == "E"].iloc[0]
        latS, lonS = S["Latitude"], S["Longitude"]
        latE, lonE = E["Latitude"], E["Longitude"]
        ref_lat, ref_lon = latS, lonS
        sx, sy = latlon_to_meters(latS, lonS, ref_lat, ref_lon)
        ex, ey = latlon_to_meters(latE, lonE, ref_lat, ref_lon)
        dx_r = ex - sx
        dy_r = ey - sy
        norm_r = math.hypot(dx_r, dy_r)
        if norm_r < 1e-9:
            dx_r, dy_r = 1.0, 0.0
            norm_r = 1.0
        row_map[row_val] = (ref_lat, ref_lon, dx_r, dy_r, norm_r)

    vines_by_row = {}
    for row_val in df_vines["Row"].unique():
        if row_val not in row_map:
            continue
        subset_v = df_vines[df_vines["Row"] == row_val].copy()
        ref_lat, ref_lon, dx_r, dy_r, norm_r = row_map[row_val]

        vine_list = []
        for _, v in subset_v.iterrows():
            ID_ = int(v["ID"])
            s_st = project_point_on_row(v["Coverage_Start_Lon"], v["Coverage_Start_Lat"], ref_lat, ref_lon, dx_r, dy_r, norm_r)
            s_ed = project_point_on_row(v["Coverage_End_Lon"], v["Coverage_End_Lat"], ref_lat, ref_lon, dx_r, dy_r, norm_r)
            s_min = min(s_st, s_ed)
            s_max = max(s_st, s_ed)
            vine_list.append((ID_, s_min, s_max))
        vines_by_row[row_val] = vine_list

    for i in range(len(df_imgs)):
        row_val = df_imgs.at[i, "Assigned_Row"]
        if row_val not in row_map:
            continue
        ref_lat, ref_lon, dx_r, dy_r, norm_r = row_map[row_val]

        left_lon  = df_imgs.at[i, "FOV_Left_Long"]
        left_lat  = df_imgs.at[i, "FOV_Left_Lat"]
        right_lon = df_imgs.at[i, "FOV_Right_Long"]
        right_lat = df_imgs.at[i, "FOV_Right_Lat"]

        if pd.isna(left_lon) or pd.isna(right_lon):
            continue

        s_left  = project_point_on_row(left_lon,  left_lat,  ref_lat, ref_lon, dx_r, dy_r, norm_r)
        s_right = project_point_on_row(right_lon, right_lat, ref_lat, ref_lon, dx_r, dy_r, norm_r)
        fov_s_min = min(s_left, s_right)
        fov_s_max = max(s_left, s_right)

        covered_vines = []
        for (vineID, vine_s_min, vine_s_max) in vines_by_row[row_val]:
            if vine_s_max < fov_s_min or vine_s_min > fov_s_max:
                continue
            covered_vines.append(f"{int(row_val)}-{int(vineID)}")

        if covered_vines:
            df_imgs.at[i, "Covered_Vines"] = ",".join(covered_vines)

    return df_imgs
