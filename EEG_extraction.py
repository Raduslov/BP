import numpy as np
from influxdb_client import InfluxDBClient, Point
from datetime import datetime, timedelta
from cassandra.cluster import Cluster
import time

file_paths = [
    'C:/Users/Rado/Downloads/Desktop/BP/DATA EEG/sub-004/eeg/sub-01_task-agencyRT_eeg.eeg',
    'C:/Users/Rado/Downloads/Desktop/BP/DATA EEG/sub-004/eeg/sub-02_task-agencyRT_eeg.eeg',
    'C:/Users/Rado/Downloads/Desktop/BP/DATA EEG/sub-004/eeg/sub-03_task-agencyRT_eeg.eeg',
    'C:/Users/Rado/Downloads/Desktop/BP/DATA EEG/sub-004/eeg/sub-04_task-agencyRT_eeg.eeg',

]

def load_eeg_data(file_path, num_channels):
    binary_data = np.fromfile(file_path, dtype=np.float32)
    channel_data_list = [binary_data[i::num_channels] for i in range(num_channels)]
    return channel_data_list

def compute_fft(data, sampling_rate):
    fft_result = np.fft.fft(data)
    freqs = np.fft.fftfreq(len(data), 1 / sampling_rate)
    return fft_result, np.abs(freqs)

def identify_eeg_waves(freqs):
    eeg_waves = []
    for freq in freqs:
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
            eeg_waves.append("Gamma")
    return eeg_waves

def create_timestamps(num_samples, sampling_interval):
    timestamps = [datetime.utcnow() + timedelta(microseconds=i*sampling_interval) for i in range(num_samples)]
    return timestamps[:2000]  

def process_eeg_file(file_path, index, cassandra_session):
    num_channels = 128  
    channel_data_list = load_eeg_data(file_path, num_channels)
    sampling_interval = 1953.125  
    timestamps = create_timestamps(len(channel_data_list[0]), sampling_interval)
    num_timestamps = len(timestamps)  

    influx_original_data_points = []
    cassandra_data_points_original = []

    start_time_processing = time.time()  # Začátek zpracování nahrávky

    for channel_index in range(num_channels):
        channel_data = channel_data_list[channel_index]

        for timestamp_index, timestamp in enumerate(timestamps):
            data_point = Point(f"Nahravka{index}_Original") \
                .tag("channel", f"channel_{channel_index + 1}") \
                .time(timestamp) \
                .field("value", float(channel_data[timestamp_index]))
            influx_original_data_points.append(data_point)

            cassandra_data_points_original.append((channel_index + 1, timestamps[timestamp_index], float(channel_data[timestamp_index])))

    # Uložení původních dat do InfluxDB
    start_time_influx_original = time.time()
    try:
        influx_token = "00Z-HfAL3ik1Z1CBmN6nVmREtRyRz4VDzOiefI8EqwS8B3WNfmU1hHG8w6MXdP0tGl5ZiAYPdS3HTzNV9AsVeA=="
        influx_org = "TUKE"
        influx_bucket = "Meranie4" 
        influx_client = InfluxDBClient(url="http://localhost:8086", token=influx_token, org=influx_org)
        influx_result = influx_client.write_api().write(bucket=influx_bucket, record=influx_original_data_points)
        end_time_influx_original = time.time()
        time_influx_original_seconds = end_time_influx_original - start_time_influx_original
        print(f"Time taken to upload original data to InfluxDB: {time_influx_original_seconds:.2f} seconds")
    except Exception as e:
        print(f"Error saving data to InfluxDB (Original): {e}")

    # Uložení původních dat do Cassandra
    start_time_cassandra_original = time.time()
    insert_original_query = cassandra_session.prepare("INSERT INTO nahravka{}_original (channel, time, value) VALUES (?, ?, ?)".format(index))
   
    for data_point in cassandra_data_points_original:
        cassandra_session.execute(insert_original_query, data_point)
    end_time_cassandra_original = time.time()
    time_cassandra_original_seconds = end_time_cassandra_original - start_time_cassandra_original
    print(f"Time taken to upload original data to Cassandra: {time_cassandra_original_seconds / 60:.2f} minutes")

    # Zpracování FFT a zápis do InfluxDB pro každý kanál
    start_time_influx_fft = time.time()
    influx_data_points = []
    for channel_index in range(num_channels):
        channel_data = channel_data_list[channel_index]
        fft_result, freqs = compute_fft(channel_data, 1 / (sampling_interval / 1e6))
        eeg_waves = identify_eeg_waves(freqs)

        for timestamp_index in range(num_timestamps):  
            # Ukládání do InfluxDB pro FFT data
            data_point = Point(f"Nahravka{index}_FFT") \
                .tag("channel", f"channel_{channel_index + 1}") \
                .time(timestamps[timestamp_index]) \
                .field("value", float(fft_result.real[timestamp_index])) \
                .tag("eeg_wave", eeg_waves[timestamp_index])
            influx_data_points.append(data_point)

    # Uložení FFT dat do InfluxDB
    try:
        influx_result = influx_client.write_api().write(bucket=influx_bucket, record=influx_data_points)
        end_time_influx_fft = time.time()
        time_influx_fft_seconds = end_time_influx_fft - start_time_influx_fft
        print(f"Time taken to upload FFT data to InfluxDB: {time_influx_fft_seconds / 60:.2f} seconds")
    except Exception as e:
        print(f"Error saving data to InfluxDB (FFT): {e}")

    # Uložení FFT dat do Cassandra
    start_time_cassandra_fft = time.time()
    insert_fft_query = cassandra_session.prepare("INSERT INTO nahravka{}_fft (channel, time, value, eeg_wave) VALUES (?, ?, ?, ?)".format(index))
    for channel_index in range(num_channels):
        channel_data = channel_data_list[channel_index]
        fft_result, freqs = compute_fft(channel_data, 1 / (sampling_interval / 1e6))
        eeg_waves = identify_eeg_waves(freqs)
        
        for timestamp_index in range(num_timestamps):  
            cassandra_data_point_fft = (channel_index + 1, timestamps[timestamp_index], float(fft_result.real[timestamp_index]), eeg_waves[timestamp_index])
            cassandra_session.execute(insert_fft_query, cassandra_data_point_fft)
    end_time_cassandra_fft = time.time()
    time_cassandra_fft_seconds = end_time_cassandra_fft - start_time_cassandra_fft
    print(f"Time taken to upload FFT data to Cassandra: {time_cassandra_fft_seconds / 60:.2f} minutes")
    
    end_time_processing = time.time()  # Konec zpracování nahrávky
    total_processing_time_seconds = end_time_processing - start_time_processing
   
    # Výpis celkového času zpracování nahrávky
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
