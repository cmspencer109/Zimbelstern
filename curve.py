import math

def log_curve_points(start, end, num_points):
    # Ensure start is greater than end
    if start <= end:
        raise ValueError("Start value must be greater than end value")

    # Calculate the scaling factor
    scale_factor = (end - start) / math.log10(1 + num_points)

    # Generate the logarithmic curve points
    points = [int(start + scale_factor * math.log10(1 + i)) for i in range(num_points)]

    return points

# Example usage:
start_value = 750
end_value = 100
num_points = 10

result = log_curve_points(start_value, end_value, num_points)
print(result)
