from utils.plotData import (
    plot_all_raw_data,
    plot_direction_figure,
    plot_camera_with_direction,
    plot_camera_by_assigned_row,
    plot_random_fov_projection,
    visualize_matched_vines
)
from utils.getMovingDirection import compute_moving_direction
from utils.getCameraPosition import compute_camera_positions
from utils.getCaptureRow import assign_image_rows
from utils.getFOVintersections import compute_fov_intersections
from utils.getVineCoverage import compute_vine_coverage_variable
from utils.matchVinesInCamFOV import match_vines_in_fov
import argparse
import gc
import os

def main():
    """
    Main pipeline entry.
    Step 0: compute grapevine coverage region
    Step 1: movement direction (F/B)
    Step 2: camera position offset to left
    Step 3: assign each camera to closest row
    Step 4: compute FOV intersections on row
    Step 5: match covered vines based on FOV
    Optionally visualize:
      --check_raw_data: visual inspection of raw layout
      --check_direction: movement direction check
      --check_camera: camera + row + F/B direction
      --check_assigned_row: colored camera points by row
      --fov_samples N: visualize N random FOV projections
      --visualize_vine_cam N: visualize N samples with camera, FOV, and matched vines
    """
    parser = argparse.ArgumentParser(description="Main pipeline for image segegration based on Geo-reference data.")
    parser.add_argument("--check_raw_data", action="store_true", help="Visualize raw data: Grapevines, GPS, and Row.")
    parser.add_argument("--check_direction", action="store_true", help="Visualize GPS points by classified movement direction.")
    parser.add_argument("--check_camera", action="store_true", help="Visualize camera positions with row vectors and direction.")
    parser.add_argument("--check_assigned_row", action="store_true", help="Visualize camera points colored by assigned row.")
    parser.add_argument("--fov_samples", type=int, default=0, help="If > 0, visualize N random FOV projection samples.")
    parser.add_argument("--visualize_vine_cam", type=int, default=0, help="If > 0, visualize N matched vine-camera images.")
    args = parser.parse_args()

    # Paths and configuration
    # ==========================================================
    grapevines_file = "Data/OBlock/Grapevines_Geo_Reference.csv"
    image_gps_file = "Data/OBlock/Image_GPS.csv"
    row_file = "Data/OBlock/Row_SE_GPS_OBlock.csv"
    grapevine_coverage_file_output_path = "Data/OBlock/Grapevines_with_Coverage.csv"
    final_output_path = "Data/OBlock/Image_GPS_FOV_matched_vines.csv"

    offset_m = 0.76
    cam_fov_degree = 60.5

    extend_first_last = 0.5
    extend_not_continuous = 1.0
    max_half_extend = 1.2
    # ==========================================================
    
    # Step 0: compute grapevine coverage and save to grapevine_coverage_file_output_path
    print("[INFO] Step 0: Computing grapevine coverage region...")
    compute_vine_coverage_variable(
        row_file=row_file,
        vine_file=grapevines_file,
        out_path=grapevine_coverage_file_output_path,
        extend_first_last=extend_first_last,
        extend_not_continuous=extend_not_continuous,
        max_half_extend=max_half_extend
    )

    # Step 1: optionally visualize raw data
    if args.check_raw_data:
        print("[INFO] Visualizing raw data for debugging/inspection...")
        plot_all_raw_data(grapevines_file, image_gps_file, row_file)
    else:
        print("[INFO] Skipping raw data visualization step...")

    # Step 2: compute movement direction
    print("[INFO] Computing movement direction classification (F/B)...")
    df_with_direction = compute_moving_direction(gps_file=image_gps_file, row_file=row_file)
    print("[Preview] First rows with direction:")
    print(df_with_direction.head())

    # Step 3: optionally visualize direction
    if args.check_direction:
        print("[INFO] Visualizing GPS points by movement direction (F/B)...")
        plot_direction_figure(df_with_direction, row_file)
    else:
        print("[INFO] Skipping direction classification visualization.")

    # Step 4: compute camera position
    print("[INFO] Computing camera positions offset to the left of motion...")
    df_with_camera = compute_camera_positions(gps_file=image_gps_file, offset_m=offset_m)

    # Step 5: merge direction + camera
    print("[INFO] Merging direction and camera position into one DataFrame...")
    df_combined = df_with_direction.copy()
    df_combined["Camera_Long"] = df_with_camera["Camera_Long"]
    df_combined["Camera_Lat"] = df_with_camera["Camera_Lat"]

    del df_with_direction, df_with_camera
    gc.collect()

    print("[Preview] Combined DataFrame (direction + camera):")
    print(df_combined.head())

    # Step 6: assign row to each camera point
    print("[INFO] Assigning nearest row to each camera position...")
    df_combined = assign_image_rows(df_combined, row_file)
    print("[Preview] Combined DataFrame with Assigned_Row:")
    print(df_combined.head())

    # Step 7: optionally visualize direction + camera layout
    if args.check_camera:
        print("[INFO] Visualizing camera positions with direction and rows...")
        plot_camera_with_direction(df_combined, row_file)
    else:
        print("[INFO] Skipping camera visualization.")

    # Step 8: optionally visualize Assigned_Row with colored camera points
    if args.check_assigned_row:
        print("[INFO] Visualizing camera points colored by assigned row...")
        plot_camera_by_assigned_row(df_combined, row_file)
    else:
        print("[INFO] Skipping Assigned_Row visualization.")

    # Step 9: compute FOV projection and intersections
    print("[INFO] Computing FOV projection intersections...")
    df_combined = compute_fov_intersections(df_combined, row_file, fov_deg=cam_fov_degree)
    print("[Preview] Combined DataFrame with FOV intersection points:")
    print(df_combined[["Image_ID", "FOV_Center_Long", "FOV_Left_Long", "FOV_Right_Long"]].head())

    # Step 10: optional FOV projection visualization
    if args.fov_samples > 0:
        print(f"[INFO] Visualizing {args.fov_samples} random FOV projection samples...")
        plot_random_fov_projection(df_combined, row_file, num_samples=args.fov_samples)
    else:
        print("[INFO] Skipping FOV projection visualization.")

    # Step 11: match covered vines based on projected FOV range
    print("[INFO] Matching grapevine coverage with camera FOV...")
    df_combined = match_vines_in_fov(df_combined, row_file, grapevine_coverage_file_output_path)
    print("[Preview] Combined DataFrame with Covered_Vines:")
    print(df_combined[["Image_ID", "Covered_Vines"]].head())

    # Step 12: save final output
    df_combined.to_csv(final_output_path, index=False)
    print(f"[INFO] Final output saved to {final_output_path}")

    # Step 13: optional visualization of vine-camera match results
    if args.visualize_vine_cam > 0:
        print(f"[INFO] Visualizing {args.visualize_vine_cam} vine-camera coverage samples...")
        visualize_matched_vines(final_output_path, grapevine_coverage_file_output_path, row_file, num_samples=args.visualize_vine_cam)
    else:
        print("[INFO] Skipping vine-camera match visualization.")


if __name__ == "__main__":
    main()
