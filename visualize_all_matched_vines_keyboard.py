import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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

class VineVisualizer:
    def __init__(self, matched_file, vine_file, row_file):
        self.df_imgs = pd.read_csv(matched_file)
        self.df_vines = pd.read_csv(vine_file)
        self.df_rows = pd.read_csv(row_file)
        self.index = 0
        self.row_map = self.build_row_map()
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        self.show_current()

    def build_row_map(self):
        row_map = {}
        for row_val in self.df_rows['Row'].unique():
            sub = self.df_rows[self.df_rows['Row'] == row_val]
            S = sub[sub['ID'] == 'S'].iloc[0]
            E = sub[sub['ID'] == 'E'].iloc[0]
            ref_lat, ref_lon = S['Latitude'], S['Longitude']
            sx, sy = latlon_to_meters(S['Latitude'], S['Longitude'], ref_lat, ref_lon)
            ex, ey = latlon_to_meters(E['Latitude'], E['Longitude'], ref_lat, ref_lon)
            dx, dy = ex - sx, ey - sy
            norm = math.hypot(dx, dy)
            if norm < 1e-9:
                dx, dy = 1.0, 0.0
                norm = 1.0
            row_map[row_val] = (ref_lat, ref_lon, dx, dy, norm)
        return row_map

    def on_key(self, event):
        if event.key == 'right':
            self.index = min(self.index + 1, len(self.df_imgs) - 1)
        elif event.key == 'left':
            self.index = max(self.index - 1, 0)
        self.show_current()

    def show_current(self):
        self.ax.clear()
        rec = self.df_imgs.iloc[self.index]
        image_id = rec["Image_ID"]
        row_val = rec["Assigned_Row"]
        if row_val not in self.row_map:
            print(f"Row {row_val} not in row_map, skipping")
            return

        cam_lon, cam_lat = rec["Camera_Long"], rec["Camera_Lat"]
        flon_l, flat_l = rec["FOV_Left_Long"], rec["FOV_Left_Lat"]
        flon_r, flat_r = rec["FOV_Right_Long"], rec["FOV_Right_Lat"]
        covered_str = str(rec.get("Covered_Vines", "")).strip()
        covered_list = []
        if covered_str:
            parts = covered_str.split(",")
            for p in parts:
                if "-" in p:
                    try:
                        r_val, v_id = map(int, p.split("-"))
                        covered_list.append((r_val, v_id))
                    except:
                        pass

        ref_lat, ref_lon, dx_r, dy_r, norm_r = self.row_map[row_val]

        self.ax.set_title(f"Image_ID={image_id}, Covered Vines: {covered_str}")

        # Draw covered grapevines FIRST (lower layer)
        subset_v = []
        for (r, vid) in covered_list:
            if r == row_val:
                cond = (self.df_vines["Row"] == r) & (self.df_vines["ID"] == vid)
                tmp = self.df_vines[cond]
                if not tmp.empty:
                    subset_v.append(tmp.iloc[0])

        for j, vine in enumerate(subset_v):
            vine_lon = vine["Longitude"]
            vine_lat = vine["Latitude"]
            st_lon = vine["Coverage_Start_Lon"]
            st_lat = vine["Coverage_Start_Lat"]
            ed_lon = vine["Coverage_End_Lon"]
            ed_lat = vine["Coverage_End_Lat"]
            v_id = vine["ID"]
            self.ax.scatter(vine_lon, vine_lat, color='blue', label='Vine Root' if j == 0 else None, zorder=1)
            self.ax.plot([st_lon, ed_lon], [st_lat, ed_lat], '-', color='green', label='Vine Coverage' if j == 0 else None, zorder=1)
            self.ax.scatter([st_lon, ed_lon], [st_lat, ed_lat], color='green', s=40, zorder=1)
            self.ax.text(vine_lon, vine_lat, f"ID={v_id}", fontsize=8, color='blue', zorder=3)

        # Draw row center line
        cx, cy = latlon_to_meters(cam_lat, cam_lon, ref_lat, ref_lon)
        center_s = cx * (dx_r / norm_r) + cy * (dy_r / norm_r)
        tvals = np.linspace(center_s - 1.0, center_s + 1.0, 2)
        pts = []
        for s in tvals:
            x = s * (dx_r / norm_r)
            y = s * (dy_r / norm_r)
            lat, lon = meters_to_latlon(x, y, ref_lat, ref_lon)
            pts.append([lon, lat])
        pts = np.array(pts)
        self.ax.plot(pts[:, 0], pts[:, 1], '--', color='gray', label='Row Local', zorder=0)

        # Draw FOV projection (TOP layer)
        if not pd.isna(flon_l) and not pd.isna(flon_r):
            self.ax.plot([flon_l, flon_r], [flat_l, flat_r], '-', color='orange', label='FOV Coverage', linewidth=2, zorder=10)
            self.ax.scatter([flon_l, flon_r], [flat_l, flat_r], color='red', s=40, label='FOV Bounds', zorder=10)

        # Draw camera point
        self.ax.scatter(cam_lon, cam_lat, color='black', s=60, label='Camera', zorder=11)

        self.ax.set_xlabel("Longitude")
        self.ax.set_ylabel("Latitude")
        self.ax.legend()
        self.ax.grid(True)
        self.fig.canvas.draw()


if __name__ == "__main__":
    matched_file = "Data/OBlock/Image_GPS_FOV_matched_vines.csv"
    vine_file = "Data/OBlock/Grapevines_with_Coverage.csv"
    row_file = "Data/OBlock/Row_SE_GPS_OBlock.csv"

    viewer = VineVisualizer(matched_file, vine_file, row_file)
    plt.show()
