import pandas as pd
import numpy as np
import argparse

# -----------------------------
# Argument parser for CLI input
# -----------------------------
parser = argparse.ArgumentParser(description="Project grapevine GPS points onto row centerlines.")

parser.add_argument('--row_se_file_path', type=str, default='/home/yl3663/General_Pipeline/Image_Segregation/Data/OBlock/Row_SE_GPS_OBlock.csv',
                    help='Path to the CSV file containing row start and end points.')
parser.add_argument('--grapevine_file_path', type=str, default='/home/yl3663/General_Pipeline/Image_Segregation/Data/OBlock/Grapevine_GPS_OBlock.csv',
                    help='Path to the CSV file containing grapevine GPS data.')
parser.add_argument('--output_file_path', type=str, default='/home/yl3663/General_Pipeline/Image_Segregation/Data/OBlock/Grapevines_Geo_Reference.csv',
                    help='Path to save the projected grapevine coordinates.')

args = parser.parse_args()

# -----------------------------
# Load data
# -----------------------------
row_se_data = pd.read_csv(args.row_se_file_path)
grapevine_data = pd.read_csv(args.grapevine_file_path)

# Extract the starting and ending points for each row
start_end_points = {}
for _, row in row_se_data.iterrows():
    row_id = row['Row']
    point_id = row['ID']
    longitude = row['Longitude']
    latitude = row['Latitude']
    
    if row_id not in start_end_points:
        start_end_points[row_id] = {}

    if point_id == 'S':
        start_end_points[row_id]['start'] = np.array([longitude, latitude])
    elif point_id == 'E':
        start_end_points[row_id]['end'] = np.array([longitude, latitude])

# -----------------------------
# Project a point to a line
# -----------------------------
def project_point_to_line(point, line_start, line_end):
    line_vec = line_end - line_start
    point_vec = point - line_start
    line_len = np.dot(line_vec, line_vec)
    projection = np.dot(point_vec, line_vec) / line_len
    projected_point = line_start + projection * line_vec
    return projected_point

# -----------------------------
# Project grapevine coordinates
# -----------------------------
projected_grapevine_data = grapevine_data.copy()

for row_id, group in grapevine_data.groupby('Row'):
    if row_id in start_end_points:
        start_point = start_end_points[row_id].get('start')
        end_point = start_end_points[row_id].get('end')
        
        if start_point is not None and end_point is not None:
            for idx in group.index:
                original_point = group.loc[idx, ['Longitude', 'Latitude']].values.astype(float)
                projected_point = project_point_to_line(original_point, start_point, end_point)
                projected_grapevine_data.at[idx, 'Longitude'] = round(projected_point[0], 8)
                projected_grapevine_data.at[idx, 'Latitude'] = round(projected_point[1], 8)

# -----------------------------
# Save results
# -----------------------------
columns_to_keep = ['Row', 'ID', 'Longitude', 'Latitude']
projected_grapevine_data = projected_grapevine_data[columns_to_keep]
projected_grapevine_data.to_csv(args.output_file_path, index=False)

print(f"Projected data saved to: {args.output_file_path}")
