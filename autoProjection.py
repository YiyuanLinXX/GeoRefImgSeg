import pandas as pd
import numpy as np

# Load the two CSV files: one for the row start-end points and one for the grapevine data points
row_se_file_path = '/home/yl3663/General_Pipeline/Image_Segregation/Data/OBlock/Row_SE_GPS_OBlock.csv'
grapevine_file_path = '/home/yl3663/General_Pipeline/Image_Segregation/Data/OBlock/Grapevine_GPS_OBlock.csv'


# Read the two files
row_se_data = pd.read_csv(row_se_file_path)
grapevine_data = pd.read_csv(grapevine_file_path)

# Extract the starting and ending points for each row
start_end_points = {}

# Extracting starting and ending points
for _, row in row_se_data.iterrows():
    row_id = row['Row']  # Row number
    point_id = row['ID']  # Point type (S or E)
    longitude = row['Longitude']
    latitude = row['Latitude']
    
    if row_id not in start_end_points:
        start_end_points[row_id] = {}

    if point_id == 'S':
        start_end_points[row_id]['start'] = np.array([longitude, latitude])
    elif point_id == 'E':
        start_end_points[row_id]['end'] = np.array([longitude, latitude])

# Function to project a point onto a line defined by two endpoints
def project_point_to_line(point, line_start, line_end):
    """
    Projects a point onto a line defined by line_start and line_end.

    Parameters:
        point (array): The point to be projected.
        line_start (array): The starting point of the line.
        line_end (array): The ending point of the line.

    Returns:
        array: The projected point on the line.
    """
    line_vec = line_end - line_start  # Vector from line_start to line_end
    point_vec = point - line_start  # Vector from line_start to the point
    line_len = np.dot(line_vec, line_vec)  # Square of the length of the line vector
    projection = np.dot(point_vec, line_vec) / line_len  # Projection scalar
    projected_point = line_start + projection * line_vec  # The projected point
    return projected_point

# Create a new DataFrame to store the projected tree locations
projected_grapevine_data = grapevine_data.copy()

# Loop through each row in the row_start_end_points to match with the grapevine data
for row_id, group in grapevine_data.groupby('Row'):
    # Check if this row ID exists in start_end_points
    if row_id in start_end_points:
        start_point = start_end_points[row_id].get('start')
        end_point = start_end_points[row_id].get('end')
        
        if start_point is not None and end_point is not None:
            # Project each tree point onto the line defined by the starting and ending points
            for idx in group.index:
                original_point = group.loc[idx, ['Longitude', 'Latitude']].values.astype(float)
                projected_point = project_point_to_line(original_point, start_point, end_point)

                # Update the longitude and latitude in the projected DataFrame
                projected_grapevine_data.at[idx, 'Longitude'] = round(projected_point[0], 8)
                projected_grapevine_data.at[idx, 'Latitude'] = round(projected_point[1], 8)

# Keep only the relevant columns in the projected DataFrame
columns_to_keep = ['Row', 'ID', 'Longitude', 'Latitude']
projected_grapevine_data = projected_grapevine_data[columns_to_keep]

# Save the projected points to a new CSV file
output_file_path = '/home/yl3663/General_Pipeline/Image_Segregation/Data/OBlock/Grapevines_Geo_Reference.csv'

projected_grapevine_data.to_csv(output_file_path, index=False)

print(f"Projected data saved to: {output_file_path}")
