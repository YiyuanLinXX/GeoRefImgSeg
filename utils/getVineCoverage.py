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

def meters_to_latlon(x, y, ref_lat, ref_lon):
    lat = y / 111320.0 + ref_lat
    lon = x / (111320.0 * math.cos(math.radians(ref_lat))) + ref_lon
    return lat, lon

def compute_vine_coverage_variable(row_file, vine_file, out_path,
                                    extend_first_last=0.5,
                                    extend_not_continuous=1.0,
                                    max_half_extend=1.2):
    cover_cfg = {
        "extend_first_last": extend_first_last,
        "extend_not_continuous": extend_not_continuous,
        "max_half_extend": max_half_extend
    }

    df_rows = pd.read_csv(row_file)
    row_map = {}

    for row_val in df_rows['Row'].unique():
        sub = df_rows[df_rows['Row'] == row_val]
        srow = sub[sub['ID'] == 'S'].iloc[0]
        erow = sub[sub['ID'] == 'E'].iloc[0]
        latS, lonS = srow["Latitude"], srow["Longitude"]
        latE, lonE = erow["Latitude"], erow["Longitude"]
        ref_lat, ref_lon = latS, lonS
        sx, sy = latlon_to_meters(latS, lonS, ref_lat, ref_lon)
        ex, ey = latlon_to_meters(latE, lonE, ref_lat, ref_lon)
        dx = ex - sx
        dy = ey - sy
        norm_d = math.hypot(dx, dy)
        if norm_d < 1e-9:
            dx, dy = 1.0, 0.0
            norm_d = 1.0
        row_map[row_val] = (ref_lat, ref_lon, dx, dy, norm_d)

    df_vines = pd.read_csv(vine_file)
    df_vines["Coverage_Start_Lon"] = np.nan
    df_vines["Coverage_Start_Lat"] = np.nan
    df_vines["Coverage_End_Lon"]   = np.nan
    df_vines["Coverage_End_Lat"]   = np.nan

    grouped = df_vines.groupby("Row")

    for row_val, group in grouped:
        if row_val not in row_map:
            continue
        ref_lat, ref_lon, dx_r, dy_r, norm_d = row_map[row_val]
        direction_unit = np.array([dx_r, dy_r]) / norm_d

        vine_info = []
        for i, row_vine in group.iterrows():
            vine_lat = row_vine["Latitude"]
            vine_lon = row_vine["Longitude"]
            vx, vy = latlon_to_meters(vine_lat, vine_lon, ref_lat, ref_lon)
            s_i = vx*direction_unit[0] + vy*direction_unit[1]
            vine_info.append((row_vine["ID"], s_i, i))

        vine_info.sort(key=lambda x: x[0])

        for idx_v in range(len(vine_info)):
            ID_i, s_i, orig_idx = vine_info[idx_v]

            if idx_v == 0:
                coverage_start = s_i - cover_cfg["extend_first_last"]
            else:
                ID_prev, s_prev, _ = vine_info[idx_v - 1]
                if ID_i - ID_prev == 1:
                    half_dist = (s_i - s_prev)/2.0
                    capped_half = min(half_dist, cover_cfg["max_half_extend"])
                    coverage_start = s_i - capped_half
                else:
                    coverage_start = s_i - cover_cfg["extend_not_continuous"]

            if idx_v == len(vine_info) - 1:
                coverage_end = s_i + cover_cfg["extend_first_last"]
            else:
                ID_next, s_next, _ = vine_info[idx_v + 1]
                if ID_next - ID_i == 1:
                    half_dist = (s_next - s_i)/2.0
                    capped_half = min(half_dist, cover_cfg["max_half_extend"])
                    coverage_end = s_i + capped_half
                else:
                    coverage_end = s_i + cover_cfg["extend_not_continuous"]

            cx_start = coverage_start*direction_unit[0]
            cy_start = coverage_start*direction_unit[1]
            cx_end   = coverage_end*direction_unit[0]
            cy_end   = coverage_end*direction_unit[1]

            lat_start, lon_start = meters_to_latlon(cx_start, cy_start, ref_lat, ref_lon)
            lat_end,   lon_end   = meters_to_latlon(cx_end,   cy_end,   ref_lat, ref_lon)

            df_vines.at[orig_idx, "Coverage_Start_Lon"] = lon_start
            df_vines.at[orig_idx, "Coverage_Start_Lat"] = lat_start
            df_vines.at[orig_idx, "Coverage_End_Lon"]   = lon_end
            df_vines.at[orig_idx, "Coverage_End_Lat"]   = lat_end

    df_vines.to_csv(out_path, index=False)
    print(f"\u2705 Coverage data saved to {out_path} with adjustable config: {cover_cfg}")