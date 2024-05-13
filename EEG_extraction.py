# Import necessary libraries
import numpy as np  # For numerical computing
from influxdb_client import InfluxDBClient, Point  # For interacting with InfluxDB
from datetime import datetime, timedelta  # For handling timestamps
from cassandra.cluster import Cluster  # For interacting with Cassandra database
import time  # For measuring time intervals

# List of file paths containing EEG data
file_paths = [
    'C:/Users/Rado/Downloads/Desktop/BP/DATA EEG/sub-004/eeg/sub-01_task-agencyRT_eeg.eeg',
    'C:/Users/Rado/Downloads/Desktop/BP/DATA EEG/sub-004/eeg/sub-02_task-agencyRT_eeg.eeg',
    'C:/Users/Rado/Downloads/Desktop/BP/DATA EEG/sub-004/eeg/sub-03_task-agencyRT_eeg.eeg',
    'C:/Users/Rado/Downloads/Desktop/BP/DATA EEG/sub-004/eeg/sub-04_task-agencyRT_eeg.eeg',
]

# Function to load EEG data from a file
def load_eeg_data(file_path, num_channels):
    # Load binary data from file
    binary_data = np.fromfile(file_path, dtype=np.float32)
    # Split data into channels
    channel_data_list = [binary_data[i::num_channels] for i in range(num_channels)]
    return channel_data_list

# Function to compute Fast Fourier Transform (FFT) of EEG data
def compute_fft(data, sampling_rate):
    fft_result = np.fft.fft(data)  # Compute FFT
    freqs = np.fft.fftfreq(len(data), 1 / sampling_rate)  # Frequency bins
    return fft_result, np.abs(freqs)

# Function to identify EEG waves based on frequency
def identify_eeg_waves(freqs):
    eeg_waves = []
    for freq in freqs:
        # Identify EEG wave based on frequency range
        if 0.5 <= freq < 4:
            eeg_waves.append("Delta")
        elif 4 <= freq < 8:
            eeg_waves.append("Theta")
        elif 8 <= freq < 13:
            eeg_waves.append("Alpha")
        elif 13 <= freq < 30:
            eeg_waves.append("Beta")
        elif 30 <= freq < 45:
            eeg_waves.append("Gamma")
        else:
            eeg_waves.append("Gamma")  # Default to Gamma if frequency doesn't match known ranges
    return eeg_waves

# Function to create timestamps for EEG data samples
def create_timestamps(num_samples, sampling_interval):
    timestamps = [datetime.utcnow() + timedelta(microseconds=i*sampling_interval) for i in range(num_samples)]
    return timestamps[:2000]  # Limit to 2000 timestamps

# Function to process EEG file
def process_eeg_file(file_path, index, cassandra_session):
    # Number of EEG channels
    num_channels = 128  
    # Load EEG data from file
    channel_data_list = load_eeg_data(file_path, num_channels)
    # Sampling interval in microseconds
    sampling_interval = 1953.125  
    # Create timestamps for EEG samples
    timestamps = create_timestamps(len(channel_data_list[0]), sampling_interval)
    # Total number of timestamps
    num_timestamps = len(timestamps)  

    # Lists to store data points for InfluxDB and Cassandra
    influx_original_data_points = []
    cassandra_data_points_original = []

    # Start processing time
    start_time_processing = time.time()  

    # Iterate over each EEG channel
    for channel_index in range(num_channels):
        channel_data = channel_data_list[channel_index]

        # Iterate over each timestamp
        for timestamp_index, timestamp in enumerate(timestamps):
            # Create InfluxDB data point
            data_point = Point(f"Nahravka{index}_Original") \
                .tag("channel", f"channel_{channel_index + 1}") \
                .time(timestamp) \
                .field("value", float(channel_data[timestamp_index]))
            influx_original_data_points.append(data_point)

            # Create Cassandra data point
            cassandra_data_points_original.append((channel_index + 1, timestamps[timestamp_index], float(channel_data[timestamp_index])))

    # Upload original data to InfluxDB
    start_time_influx_original = time.time()
    # Connect to InfluxDB and write data points
    try:
        influx_token = "your_influxdb_token_here"
        influx_org = "TUKE"
        influx_bucket = "Meranie4" 
        influx_client = InfluxDBClient(url="http://localhost:8086", token=influx_token, org=influx_org)
        influx_result = influx_client.write_api().write(bucket=influx_bucket, record=influx_original_data_points)
        end_time_influx_original = time.time()
        time_influx_original_seconds = end_time_influx_original - start_time_influx_original
        print(f"Time taken to upload original data to InfluxDB: {time_influx_original_seconds:.2f} seconds")
    except Exception as e:
        print(f"Error saving data to InfluxDB (Original): {e}")

    # Upload original data to Cassandra
    start_time_cassandra_original = time.time()
    # Prepare INSERT query for Cassandra
    insert_original_query = cassandra_session.prepare("INSERT INTO nahravka{}_original (channel, time, value) VALUES (?, ?, ?)".format(index))
    # Execute INSERT queries
    for data_point in cassandra_data_points_original:
        cassandra_session.execute(insert_original_query, data_point)
    end_time_cassandra_original = time.time()
    time_cassandra_original_seconds = end_time_cassandra_original - start_time_cassandra_original
    print(f"Time taken to upload original data to Cassandra: {time_cassandra_original_seconds / 60:.2f} minutes")

    # More processing steps follow...

    # End processing time
    end_time_processing = time.time()  
    # Total processing time
    total_processing_time_seconds = end_time_processing - start_time_processing
   
    # Print total processing time
    print(f"Total processing time for Nahravka{index}: {total_processing_time_seconds / 60:.2f} minutes")
    return total_processing_time_seconds

# Connect to Cassandra
cassandra_cluster = Cluster(['127.0.0.1'])
cassandra_session = cassandra_cluster.connect()

# Create Keyspace if not exists
cassandra_session.execute("""
    CREATE KEYSPACE IF NOT EXISTS meranie4
    WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};
""")

# Switch to the keyspace
cassandra_session.set_keyspace('meranie4')

# Create original and FFT tables in Cassandra
for index in range(1, len(file_paths) + 1):
    original_table_query = f"""
        CREATE TABLE IF NOT EXISTS nahravka{index}_original (
            channel INT,
            time TIMESTAMP,
            value FLOAT,
            PRIMARY KEY (channel, time)
        );
    """

    fft_table_query = f"""
        CREATE TABLE IF NOT EXISTS nahravka{index}_fft (
            channel INT,
            time TIMESTAMP,
            value FLOAT,
            eeg_wave TEXT,
            PRIMARY KEY (channel, time)
        );
    """
    try:
        cassandra_session.execute(original_table_query)
        cassandra_session.execute(fft_table_query)
    except Exception as e:
        print(f"Error creating tables for nahravka{index}: {e}")

    # Create index on eeg_wave column
    try:
        cassandra_session.execute(f"""
            CREATE INDEX IF NOT EXISTS eeg_wave_index ON meranie4.nahravka{index}_fft(eeg_wave);
        """)
    except Exception as e:
        print(f"Error creating index on eeg_wave for nahravka{index}_fft: {e}")

# Processing each EEG file
total_processing_times = []
for index, file_path in enumerate(file_paths, start=1):
    processing_time = process_eeg_file(file_path, index, cassandra_session)
    total_processing_times.append(processing_time)

# Close Cassandra session
cassandra_session.shutdown()
