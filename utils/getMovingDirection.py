import pandas as pd
import math

def compute_moving_direction(
    gps_file="Data/OBlock/Image_GPS.csv",
    row_file="Data/OBlock/Row_SE_GPS_OBlock.csv"
):
    """
    Reads gps_file (Image_GPS.csv) and row_file (Row_SE_GPS_OBlock.csv),
    computes robot moving direction vs. average row direction,
    classifies each data point as 'F' (forward, same direction as row vector direction) or 'B' (backward, opposite direction as row vector direction),
    returns a DataFrame with an additional column 'Direction'.
    """
    df_img = pd.read_csv(gps_file)
    df_img = df_img.sort_values(by="Image_ID").reset_index(drop=True)

    # Step 1: Compute average global row direction vector
    df_row = pd.read_csv(row_file)
    v_vectors = []
    for row_val in df_row['Row'].unique():
        subdf = df_row[df_row['Row'] == row_val]
        start = subdf[subdf['ID'] == 'S']
        end   = subdf[subdf['ID'] == 'E']
        if not start.empty and not end.empty:
            dx = end.iloc[0]["Longitude"] - start.iloc[0]["Longitude"]
            dy = end.iloc[0]["Latitude"]  - start.iloc[0]["Latitude"]
            v_vectors.append((dx, dy))

    if not v_vectors:
        V_se_unit = (1.0, 0.0)  # Default fallback
    else:
        avg_dx = sum(v[0] for v in v_vectors) / len(v_vectors)
        avg_dy = sum(v[1] for v in v_vectors) / len(v_vectors)
        norm = math.hypot(avg_dx, avg_dy)
        if norm < 1e-6:
            V_se_unit = (1.0, 0.0)
        else:
            V_se_unit = (avg_dx / norm, avg_dy / norm)

    # Step 2: Compute movement direction between consecutive GPS points
    directions = []
    n = len(df_img)
    for i in range(n):
        if i < n - 1:
            curr_id = int(df_img.iloc[i]["Image_ID"])
            next_id = int(df_img.iloc[i + 1]["Image_ID"])
            if next_id - curr_id == 1:
                dx = df_img.iloc[i + 1]["Longitude"] - df_img.iloc[i]["Longitude"]
                dy = df_img.iloc[i + 1]["Latitude"]  - df_img.iloc[i]["Latitude"]
                mag = math.hypot(dx, dy)
                if mag < 1e-6:
                    directions.append("F")
                else:
                    dot = dx * V_se_unit[0] + dy * V_se_unit[1]
                    directions.append("F" if dot >= 0 else "B")
            else:
                directions.append(directions[i - 1] if i > 0 else "F")
        else:
            directions.append(directions[i - 1] if i > 0 else "F")

    df_img["Direction"] = directions
    return df_img
