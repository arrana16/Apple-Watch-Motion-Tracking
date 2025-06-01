import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation as R

# Load the dataset and split tables
def load_and_split_data(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Find the line where angle data starts
    angle_start_line = next(i for i, line in enumerate(lines) if "pitch" in line.lower() and "roll" in line.lower() and "yaw" in line.lower())

    # Read acceleration and angle data separately
    accel_data = pd.read_csv(file_path, nrows=angle_start_line - 1)
    angle_data = pd.read_csv(file_path, skiprows=angle_start_line)

    return accel_data, angle_data

# Clean and preprocess data
def preprocess_data(accel_data, angle_data):
    # Rename columns for clarity
    accel_data.columns = [col.strip() for col in accel_data.columns]
    angle_data.columns = [col.strip() for col in angle_data.columns]

    # Convert columns to numeric, coercing errors to NaN
    for col in ["Time", "x", "y", "z"]:
        accel_data[col] = pd.to_numeric(accel_data[col], errors="coerce")
    for col in ["Time", "pitch", "roll", "yaw"]:
        angle_data[col] = pd.to_numeric(angle_data[col], errors="coerce")

    # Print the number of NaN values in each column before dropping
    print("NaN values in accel_data before dropping:")
    print(accel_data.isna().sum())
    print("NaN values in angle_data before dropping:")
    print(angle_data.isna().sum())

    # Drop rows with NaN values in relevant columns only
    accel_data.dropna(subset=["Time", "x", "y", "z"], inplace=True)
    angle_data.dropna(subset=["Time", "pitch", "roll", "yaw"], inplace=True)

    # Print the shape of the data after dropping NaN values
    print(f"Shape of accel_data after dropping NaN values: {accel_data.shape}")
    print(f"Shape of angle_data after dropping NaN values: {angle_data.shape}")

    return accel_data, angle_data

# Match angles to acceleration data
def match_angles(accel_data, angle_data):
    # Expand angle data to match acceleration sampling rate
    expanded_angles = np.repeat(angle_data.values, 4, axis=0)[:len(accel_data)]
    angle_df = pd.DataFrame(expanded_angles, columns=angle_data.columns)

    # Merge data
    merged_data = pd.concat([accel_data.reset_index(drop=True), angle_df.reset_index(drop=True)], axis=1)

    return merged_data

# Apply a simple moving average filter to smooth the data
def apply_sma_filter(data, window_size=50):
    return data.rolling(window=window_size, center=True).mean()

# Correct acceleration using orientation
def correct_acceleration(data):
    print("Starting correct_acceleration function")
    print(f"Data shape: {data.shape}")

    # Initialize a list to store corrected accelerations
    corrected_accelerations = []

    # Apply rotation matrices to correct for gravity
    for i, row in data.iterrows():
        print(f"Processing row {i}")
        try:
            # Adjust the order of axes to match the definitions
            rotation = R.from_euler('yxz', [row["roll"], row["pitch"], row["yaw"]])
            acc = np.array([row["x"], row["y"], row["z"]]) * 9.81  # Convert G to m/s^2
            corrected_acc = rotation.apply(acc) + np.array([0, 0, 9.81])  # Add gravity
            corrected_accelerations.append(corrected_acc)
        except Exception as e:
            print(f"Error at index {i}: {e}")
            corrected_accelerations.append([np.nan, np.nan, np.nan])

    # Convert the list to a 2D numpy array
    corrected_accelerations = np.array(corrected_accelerations)

    # Check for NaN values and log the number of valid rows
    valid_rows = ~np.isnan(corrected_accelerations).any(axis=1)
    print(f"Number of valid corrected accelerations: {valid_rows.sum()} out of {len(corrected_accelerations)}")

    if valid_rows.sum() == 0:
        raise ValueError("No valid accelerations to process. Check input data.")

    # Filter out rows with NaN values
    corrected_accelerations = corrected_accelerations[valid_rows]

    # Update the data DataFrame with corrected accelerations
    data = data[valid_rows].reset_index(drop=True)
    data["x_corr"] = corrected_accelerations[:, 0]
    data["y_corr"] = corrected_accelerations[:, 1]
    data["z_corr"] = corrected_accelerations[:, 2]

    # Apply SMA filter to smooth the corrected acceleration data
    data["x_corr"] = apply_sma_filter(data["x_corr"])
    data["y_corr"] = apply_sma_filter(data["y_corr"])
    data["z_corr"] = apply_sma_filter(data["z_corr"])

    return data

# Calculate velocity and power
def calculate_velocity_and_power(data, barbell_weight, start_time, end_time):
    # Ensure the Time column is correctly formatted
    if "Time" not in data.columns:
        raise ValueError("The 'Time' column is missing from the data.")

    # Drop duplicate Time columns
    data = data.loc[:, ~data.columns.duplicated()]

    # Print the structure of the DataFrame
    print("Data columns before calculating Time_diff:")
    print(data.columns)

    # Calculate time differences in seconds
    data["Time_diff"] = data["Time"].diff().fillna(0)

    # Hard set the velocity at around start_time to 0
    reset_index = data[data["Time"] >= start_time].index[0]
    data.loc[reset_index, "x_velocity"] = 0
    data.loc[reset_index, "y_velocity"] = 0
    data.loc[reset_index, "z_velocity"] = 0

    # Estimate velocity by integrating corrected acceleration over time
    for i in range(reset_index + 1, len(data)):
        if data.loc[i, "Time"] <= end_time:
            data.loc[i, "x_velocity"] = data.loc[i - 1, "x_velocity"] + data.loc[i, "x_corr"] * data.loc[i, "Time_diff"]
            data.loc[i, "y_velocity"] = data.loc[i - 1, "y_velocity"] + data.loc[i, "y_corr"] * data.loc[i, "Time_diff"]
            data.loc[i, "z_velocity"] = data.loc[i - 1, "z_velocity"] + data.loc[i, "z_corr"] * data.loc[i, "Time_diff"]

    # Calculate the combined magnitude of all velocity components
    data["velocity_magnitude"] = np.sqrt(data["x_velocity"]**2 + data["y_velocity"]**2 + data["z_velocity"]**2)

    # Calculate power (Power = Force * Velocity; Force = mass * acceleration)
    data["power"] = barbell_weight * 9.81 * data["z_velocity"]

    # Identify peak values
    peak_velocity = data["velocity_magnitude"].max()
    peak_power = data["power"].max()

    # Calculate mean values
    mean_velocity = data["velocity_magnitude"].mean()
    mean_power = data["power"].mean()

    return data, peak_velocity, peak_power, mean_velocity, mean_power

# Plot the results
def plot_results(data, start_time=None, end_time=None):
    # Drop duplicate columns
    data = data.loc[:, ~data.columns.duplicated()]

    if start_time is None or end_time is None:
        # Cap the acceleration values at 15 m/s^2
        data["x_corr"] = np.clip(data["x_corr"], -15, 15)
        data["y_corr"] = np.clip(data["y_corr"], -15, 15)
        data["z_corr"] = np.clip(data["z_corr"], -15, 15)

        # Plot the entire corrected acceleration data
        plt.figure(figsize=(12, 18))

        # Plot uncorrected acceleration
        plt.subplot(4, 1, 1)
        plt.plot(data["Time"], data["x"], label="X Acceleration", color="red")
        plt.plot(data["Time"], data["y"], label="Y Acceleration", color="green")
        plt.plot(data["Time"], data["z"], label="Z Acceleration", color="blue")
        plt.xlabel("Time (s)")
        plt.ylabel("Acceleration (m/s^2)")
        plt.title("Uncorrected Acceleration Over Time")
        plt.legend()
        plt.grid(True)

        # Plot angle values
        plt.subplot(4, 1, 2)
        plt.plot(data["Time"], data["pitch"], label="Pitch", color="orange")
        plt.plot(data["Time"], data["roll"], label="Roll", color="purple")
        plt.plot(data["Time"], data["yaw"], label="Yaw", color="brown")
        plt.xlabel("Time (s)")
        plt.ylabel("Angle (radians)")
        plt.title("Angle Values Over Time")
        plt.legend()
        plt.grid(True)

        # Plot corrected acceleration
        plt.subplot(4, 1, 3)
        plt.plot(data["Time"], data["x_corr"], label="X Acceleration", color="red")
        plt.plot(data["Time"], data["y_corr"], label="Y Acceleration", color="green")
        plt.plot(data["Time"], data["z_corr"], label="Z Acceleration", color="blue")
        plt.xlabel("Time (s)")
        plt.ylabel("Acceleration (m/s^2)")
        plt.title("Corrected Acceleration Over Time")
        plt.legend()
        plt.grid(True)

        plt.tight_layout()
        plt.show()
    else:
        # Trim the data to only include rows within the specified time range
        trimmed_data = data[(data["Time"] >= start_time) & (data["Time"] <= end_time)]

        plt.figure(figsize=(12, 18))

        # Plot acceleration
        plt.subplot(4, 1, 1)
        plt.plot(trimmed_data["Time"], trimmed_data["x_corr"], label="X Acceleration", color="red")
        plt.plot(trimmed_data["Time"], trimmed_data["y_corr"], label="Y Acceleration", color="green")
        plt.plot(trimmed_data["Time"], trimmed_data["z_corr"], label="Z Acceleration", color="blue")
        plt.xlabel("Time (s)")
        plt.ylabel("Acceleration (m/s^2)")
        plt.title("Acceleration Over Time")
        plt.legend()
        plt.grid(True)

        # Plot velocity if it exists
        if "velocity_magnitude" in trimmed_data.columns:
            plt.subplot(4, 1, 2)
            plt.plot(trimmed_data["Time"], trimmed_data["velocity_magnitude"], label="Velocity Magnitude", color="blue")
            plt.xlabel("Time (s)")
            plt.ylabel("Velocity (m/s)")
            plt.title("Velocity Over Time")
            plt.legend()
            plt.grid(True)

        # Plot power if it exists
        if "power" in trimmed_data.columns:
            plt.subplot(4, 1, 3)
            plt.plot(trimmed_data["Time"], trimmed_data["power"], label="Power", color="purple")
            plt.xlabel("Time (s)")
            plt.ylabel("Power (W)")
            plt.title("Power Over Time")
            plt.legend()
            plt.grid(True)

        plt.tight_layout()
        plt.show()

# Main program
def main():
    file_path = "Post-Test Motion.csv"  # Replace with the correct path

    # Load and split the data
    print("Loading and splitting data")
    accel_data, angle_data = load_and_split_data(file_path)
    print(f"Acceleration data shape: {accel_data.shape}")
    print(f"Angle data shape: {angle_data.shape}")

    # Preprocess the data
    print("Preprocessing data")
    accel_data, angle_data = preprocess_data(accel_data, angle_data)
    print(f"Preprocessed acceleration data shape: {accel_data.shape}")
    print(f"Preprocessed angle data shape: {angle_data.shape}")

    # Match angles to acceleration data
    print("Matching angles to acceleration data")
    data = match_angles(accel_data, angle_data)
    print(f"Matched data shape: {data.shape}")

    # Correct acceleration for orientation and gravity
    print("Correcting acceleration")
    data = correct_acceleration(data)
    print(f"Corrected data shape: {data.shape}")

    # Plot the entire corrected acceleration data
    plot_results(data)

    # User input for the range to plot corrected acceleration values
    plot_start_time = float(input("Enter the start time (in seconds) to plot corrected acceleration values: "))
    plot_end_time = float(input("Enter the end time (in seconds) to plot corrected acceleration values: "))

    # Plot the corrected acceleration values within the specified range
    plot_results(data, plot_start_time, plot_end_time)

    # User input for time range and barbell weight
    start_time = float(input("Enter the start time (in seconds) for velocity and power calculation: "))
    end_time = float(input("Enter the end time (in seconds) for velocity and power calculation: "))
    barbell_weight = float(input("Enter the weight of the barbell (in kg): "))

    # Calculate velocity and power
    print("Calculating velocity and power")
    processed_data, peak_velocity, peak_power, mean_velocity, mean_power = calculate_velocity_and_power(data, barbell_weight, start_time, end_time)
    print(f"Peak velocity: {peak_velocity}")
    print(f"Mean velocity: {mean_velocity}")
    print(f"Peak power: {peak_power}")
    print(f"Mean power: {mean_power}")

    # Plot the results for the specified time range
    plot_results(processed_data, start_time, end_time)

if __name__ == "__main__":
    main()