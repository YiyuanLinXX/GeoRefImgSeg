import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import random
from matplotlib.patches import FancyArrow

def plot_grapevines_data(ax, grapevines_file):
    """
    Reads the entire Grapevines_Geo_Reference.csv from `grapevines_file`
    and plots the vine positions (Longitude, Latitude) in green.
    """
    df = pd.read_csv(grapevines_file)
    ax.scatter(df["Longitude"], df["Latitude"],
               c='green', label='Grapevines', marker='o')

def plot_image_gps_data(ax, image_gps_file):
    """
    Reads the entire Image_GPS.csv from `image_gps_file`
    and plots the image GPS positions (Longitude, Latitude) in purple crosses.
    """
    df = pd.read_csv(image_gps_file)
    ax.scatter(df["Longitude"], df["Latitude"],
               c='purple', label='Image GPS', marker='x')

def plot_row_vectors_data(ax, row_file):
    """
    Reads the entire Row_SE_GPS_OBlock.csv from `row_file`
    and plots row vectors from 'S' to 'E'.
    The arrow's head and shaft size are based on the distance.
    """
    df = pd.read_csv(row_file)
    row_vector_label_added = False

    for row_val in df['Row'].unique():
        subdf = df[df['Row'] == row_val]
        start = subdf[subdf['ID'] == 'S']
        end   = subdf[subdf['ID'] == 'E']

        if not start.empty and not end.empty:
            start_long = start.iloc[0]["Longitude"]
            start_lat  = start.iloc[0]["Latitude"]
            end_long   = end.iloc[0]["Longitude"]
            end_lat    = end.iloc[0]["Latitude"]

            dx = end_long - start_long
            dy = end_lat  - start_lat
            dist = math.hypot(dx, dy)

            head_size   = 0.005 * dist
            shaft_width = head_size * 0.005

            if not row_vector_label_added:
                ax.arrow(start_long, start_lat, dx, dy, width=shaft_width,
                         length_includes_head=True, head_width=head_size, head_length=head_size,
                         fc='blue', ec='blue', alpha=0.7, label='Row Vector')
                row_vector_label_added = True
            else:
                ax.arrow(start_long, start_lat, dx, dy, width=shaft_width,
                         length_includes_head=True, head_width=head_size, head_length=head_size,
                         fc='blue', ec='blue', alpha=0.7)

            ax.plot([start_long, end_long],
                    [start_lat, end_lat], 'o', color='red')

def plot_all_raw_data(grapevines_file, image_gps_file, row_file):
    """
    Creates a single plot showing:
      - Grapevines positions (green circles)
      - Raw image GPS positions (purple crosses)
      - Row vectors (blue arrows)
    reading entire CSV files in each subfunction, referencing needed columns by name.
    """
    fig, ax = plt.subplots(figsize=(10, 20))

    plot_grapevines_data(ax, grapevines_file)
    plot_image_gps_data(ax, image_gps_file)
    plot_row_vectors_data(ax, row_file)

    ax.set_title("Combined Raw Geo Data: Grapevines, Rows, and Image GPS")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend()
    ax.grid(True)
    plt.show()

def plot_direction_classification(ax, df_with_direction):
    for label, color in {"F": "yellow", "B": "purple"}.items():
        subset = df_with_direction[df_with_direction["Direction"] == label]
        ax.scatter(subset["Longitude"], subset["Latitude"],
                   c=color, label=f"Robot Position with Direction: {label}", marker='x')

def plot_direction_figure(df_with_direction, row_file):
    fig, ax = plt.subplots(figsize=(10, 20))
    plot_row_vectors_data(ax, row_file)
    plot_direction_classification(ax, df_with_direction)
    ax.set_title("Robot GPS by Moving Direction (F/B) with Row Vectors")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend()
    ax.grid(True)
    plt.show()

def plot_camera_with_direction(df_combined, row_file):
    fig, ax = plt.subplots(figsize=(10, 20))
    plot_row_vectors_data(ax, row_file)

    for label, color in {"F": "yellow", "B": "purple"}.items():
        subset = df_combined[df_combined["Direction"] == label]
        ax.scatter(subset["Longitude"], subset["Latitude"],
                   c=color, marker='x', label=f"GPS: {label}", alpha=0.6)

    ax.scatter(df_combined["Camera_Long"], df_combined["Camera_Lat"],
               c='black', marker='s', label='Camera Pos', s=5)

    ax.set_title("Camera Position with Direction & Row Vectors")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend()
    ax.grid(True)
    plt.show()

def plot_camera_by_assigned_row(df_combined, row_file):
    fig, ax = plt.subplots(figsize=(10, 20))
    plot_row_vectors_data(ax, row_file)

    unique_rows = df_combined["Assigned_Row"].unique()
    colormap = plt.cm.get_cmap("tab20", len(unique_rows))
    row_to_color = {row: colormap(i) for i, row in enumerate(sorted(unique_rows))}

    for row_val in unique_rows:
        subset = df_combined[df_combined["Assigned_Row"] == row_val]
        ax.scatter(subset["Camera_Long"], subset["Camera_Lat"],
                   color=row_to_color[row_val], label=f"Row {row_val}", s=5)

    ax.set_title("Camera Positions Colored by Assigned Row")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(markerscale=1, fontsize=8, loc='best', bbox_to_anchor=(1.01, 1.0))
    ax.grid(True)
    plt.tight_layout()
    plt.show()

def plot_random_fov_projection(df_combined, row_file, num_samples=20, window=10, fov_deg=60.5, seed=42):
    df = df_combined[df_combined['Assigned_Row'] != -1].sort_values(by='Image_ID').reset_index(drop=True)
    df_row = pd.read_csv(row_file)
    n = len(df)
    if n == 0:
        print("No valid data points with assigned row.")
        return

    random.seed(seed)
    indices = random.sample(range(n), min(num_samples, n))

    for idx in indices:
        row_data = df.iloc[idx]
        center_id = int(row_data['Image_ID'])
        cam = np.array([row_data['Camera_Long'], row_data['Camera_Lat']])
        row_val = int(row_data['Assigned_Row'])

        # FOV intersection points from DataFrame
        I_center = np.array([row_data['FOV_Center_Long'], row_data['FOV_Center_Lat']]) if not pd.isna(row_data['FOV_Center_Long']) else None
        I1 = np.array([row_data['FOV_Left_Long'], row_data['FOV_Left_Lat']]) if not pd.isna(row_data['FOV_Left_Long']) else None
        I2 = np.array([row_data['FOV_Right_Long'], row_data['FOV_Right_Lat']]) if not pd.isna(row_data['FOV_Right_Long']) else None

        start = max(0, idx - window)
        end = min(n, idx + window + 1)
        subset = df.iloc[start:end]

        fig, ax = plt.subplots(figsize=(10, 9))
        ax.set_title(f"Image_ID {center_id}, Row {row_val} (FOV Projection)")

        # draw actual row segment from row_file
        row_seg = df_row[df_row['Row'] == row_val]
        if not row_seg.empty and len(row_seg) == 2:
            s = row_seg[row_seg['ID'] == 'S'].iloc[0]
            e = row_seg[row_seg['ID'] == 'E'].iloc[0]
            ax.plot([s['Longitude'], e['Longitude']], [s['Latitude'], e['Latitude']], '-', color='blue', alpha=0.4, label=f'Row {row_val}')
            ax.text((s['Longitude'] + e['Longitude']) / 2, (s['Latitude'] + e['Latitude']) / 2,
                    f"Row {row_val}", fontsize=10, color='blue')

        ax.scatter(subset["Camera_Long"], subset["Camera_Lat"], color='gray', alpha=0.6, label='Surrounding Points')
        ax.scatter(cam[0], cam[1], color='black', s=60, label='Camera')

        if I_center is not None:
            ax.plot([cam[0], I_center[0]], [cam[1], I_center[1]], '-', color='green', alpha=0.5)
            ax.scatter(I_center[0], I_center[1], color='green', label='Center Intersection')

        if I1 is not None and I2 is not None:
            ax.plot([cam[0], I1[0]], [cam[1], I1[1]], '--', color='red')
            ax.plot([cam[0], I2[0]], [cam[1], I2[1]], '--', color='red')
            ax.scatter([I1[0], I2[0]], [I1[1], I2[1]], color='red', label='FOV Intersections')
            ax.plot([I1[0], I2[0]], [I1[1], I2[1]], '-', color='orange', label='FOV Coverage')

        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.legend()
        ax.grid(True)
        plt.tight_layout()
        plt.show()



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

def visualize_matched_vines(df_image_path, df_vine_path, row_file_path, num_samples=5, seed=42):
    df_imgs = pd.read_csv(df_image_path)
    df_vines = pd.read_csv(df_vine_path)
    df_rows = pd.read_csv(row_file_path)

    # Build row map
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
        dx = ex - sx
        dy = ey - sy
        norm = math.hypot(dx, dy)
        if norm < 1e-9:
            dx, dy = 1.0, 0.0
            norm = 1.0
        row_map[row_val] = (ref_lat, ref_lon, dx, dy, norm)

    # Randomly sample images to visualize
    random.seed(seed)
    sampled = random.sample(list(df_imgs.index), min(num_samples, len(df_imgs)))

    for i in sampled:
        row = df_imgs.iloc[i]
        image_id = row["Image_ID"]
        row_val = row["Assigned_Row"]
        cam_lon = row["Camera_Long"]
        cam_lat = row["Camera_Lat"]
        flon_l = row["FOV_Left_Long"]
        flat_l = row["FOV_Left_Lat"]
        flon_r = row["FOV_Right_Long"]
        flat_r = row["FOV_Right_Lat"]
        covered_str = str(row.get("Covered_Vines", "")).strip()

        ref_lat, ref_lon, dx, dy, norm = row_map.get(row_val, (None, None, None, None, None))
        if ref_lat is None:
            continue

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.set_title(f"Image {image_id} covers: {covered_str}")

        # Plot FOV
        ax.scatter(cam_lon, cam_lat, color='black', s=60, label='Camera')
        if not pd.isna(flon_l) and not pd.isna(flon_r):
            ax.plot([flon_l, flon_r], [flat_l, flat_r], '-', color='orange', label='FOV Coverage')
            ax.scatter([flon_l, flon_r], [flat_l, flat_r], color='red', label='FOV Bounds')

        # Plot row (local segment)
        cx, cy = latlon_to_meters(cam_lat, cam_lon, ref_lat, ref_lon)
        param_center = cx * dx / norm + cy * dy / norm
        t = np.linspace(-1, 1, 2)
        pts = []
        for offset in t:
            s = param_center + offset
            px = s * dx / norm
            py = s * dy / norm
            la, lo = meters_to_latlon(px, py, ref_lat, ref_lon)
            pts.append([lo, la])
        pts = np.array(pts)
        ax.plot(pts[:, 0], pts[:, 1], '--', color='gray', label='Row segment')

        # Plot covered vines
        covered_list = []
        if covered_str:
            for val in covered_str.split(","):
                parts = val.strip().split("-")
                if len(parts) == 2:
                    try:
                        rv = int(parts[0])
                        vid = int(parts[1])
                        if rv == row_val:
                            covered_list.append(vid)
                    except:
                        continue

        for vid in covered_list:
            cond = (df_vines["Row"] == row_val) & (df_vines["ID"] == vid)
            vine = df_vines[cond]
            if vine.empty:
                continue
            vine = vine.iloc[0]
            ax.scatter(vine["Longitude"], vine["Latitude"], color='blue', label='Vine Root')
            ax.plot([vine["Coverage_Start_Lon"], vine["Coverage_End_Lon"]],
                    [vine["Coverage_Start_Lat"], vine["Coverage_End_Lat"]], '-', color='green', label='Vine Coverage')
            ax.scatter([vine["Coverage_Start_Lon"], vine["Coverage_End_Lon"]],
                       [vine["Coverage_Start_Lat"], vine["Coverage_End_Lat"]], color='green')
            ax.text(vine["Longitude"], vine["Latitude"], f"ID={vid}", fontsize=8, color='blue')

        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.grid(True)
        ax.legend()
        plt.tight_layout()
        plt.show()