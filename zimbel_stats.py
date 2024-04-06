# Generates zimbelstern statistics from a CSV file containing zimbelstern log data

import csv
from collections import Counter

def parse_duration(duration_str):
    # Extract duration value and convert to seconds
    duration = int(duration_str.split()[0])
    return duration

def parse_tempo(tempo_str):
    # Extract tempo value
    tempo = int(tempo_str.split()[0])
    return tempo

def parse_volume(volume_str):
    # Extract volume value
    volume = int(volume_str.split()[0])
    return volume

def main():
    # Open the CSV file
    with open('zimbel_log_example.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        
        durations = []
        start_methods = []
        stop_methods = []
        tempos = []
        volumes = []
        easter_egg_count = 0  # Count for "easter egg played"
        
        for row in reader:
            if 'easter egg' in row['start_method']:  # Check if the row contains "easter egg played"
                easter_egg_count += 1
            else:
                durations.append(parse_duration(row['duration']))
                start_methods.append(row['start_method'])
                stop_methods.append(row['stop_method'])
                tempos.append(parse_tempo(row['tempo']))
                volumes.append(parse_volume(row['volume']))
        
        # Calculate statistics
        average_duration = sum(durations) / len(durations)
        longest_duration = max(durations)
        most_common_start_method = Counter(start_methods).most_common(1)[0][0]
        most_common_stop_method = Counter(stop_methods).most_common(1)[0][0]
        average_tempo = sum(tempos) / len(tempos)
        average_volume = sum(volumes) / len(volumes)
        
        start_method_counts = Counter(start_methods)
        stop_method_counts = Counter(stop_methods)
        
        # Print statistics
        print("***** Zimbelstern Statistics *****\n")
        print(f"Average duration: {int(average_duration)} seconds")
        print(f"Longest duration: {longest_duration} seconds")
        print(f"Most common start method: {most_common_start_method}")
        print(f"Most common stop method: {most_common_stop_method}")
        print(f"Average tempo: {int(average_tempo)} bpm")
        print(f"Average volume: {int(average_volume)} ms")
        print(f"Number of times easter egg played: {easter_egg_count}")
        print("\nStart method counts:")
        for method, count in start_method_counts.items():
            print(f"{method}: {count}")
        print("\nStop method counts:")
        for method, count in stop_method_counts.items():
            print(f"{method}: {count}")

if __name__ == "__main__":
    main()
