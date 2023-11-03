from django.shortcuts import render, redirect
from .models import CSVFile
import threading
import sys
import csv
from django.http import FileResponse
import os
from django.conf import settings
from django.http import HttpResponse
from django.views.static import serve



def merge(left, right, attribute):
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        left_value = left[i][attribute]
        right_value = right[j][attribute]

        # Check if the values are numeric
        if left_value.isnumeric() and right_value.isnumeric():
            left_value = float(left_value)
            right_value = float(right_value)

        if left_value < right_value:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    result += left[i:]
    result += right[j:]
    return result

def merge_sort(arr, attribute):
    if len(arr) > 1:
        mid = len(arr) // 2
        left_half = arr[:mid]
        right_half = arr[mid:]

        left_half = merge_sort(left_half, attribute)
        right_half = merge_sort(right_half, attribute)

        return merge(left_half, right_half, attribute)
    return arr

def multithreaded_merge_sort(arr, attribute, threads=4):
    if len(arr) > 1:
        if threads <= 1 or len(arr) <= 1000:  # Use a threshold for small arrays
            return merge_sort(arr, attribute)
        else:
            mid = len(arr) // 2
            left_half = arr[:mid]
            right_half = arr[mid:]

            left_thread = threading.Thread(target=multithreaded_merge_sort, args=(left_half, attribute, threads // 2))
            right_thread = threading.Thread(target=multithreaded_merge_sort, args=(right_half, attribute, threads // 2))

            left_thread.start()
            right_thread.start()

            left_thread.join()
            right_thread.join()

            return merge(left_half, right_half, attribute)

def upload_csv(request):
    if request.method == 'POST':
        uploaded_file = request.FILES['csv_file']
        if uploaded_file.name.endswith('.csv'):
            dataset = []

            # Read the dataset from the uploaded CSV file
            csv_data = uploaded_file.read().decode('utf-8').splitlines()
            csv_reader = csv.DictReader(csv_data)

            for row in csv_reader:
                dataset.append(row)

            sort_attribute = request.POST['sort_attribute']
            import time
            start_time = time.perf_counter()
            sorted_dataset = merge_sort(dataset, sort_attribute)
            end_time = time.perf_counter()
            regular_execution_time_ns = int((end_time - start_time) * 1e9)

            space_complexity = sys.getsizeof(sorted_dataset)

            start_time = time.perf_counter()
            sorted_multithreaded_dataset = multithreaded_merge_sort(dataset, sort_attribute)
            end_time = time.perf_counter()
            multithreaded_execution_time_ns = int((end_time - start_time) * 1e9)
            space_complexity_multithreaded = sys.getsizeof(sorted_multithreaded_dataset)

            # Save the sorted dataset as a new CSV file
            sorted_csv_filename = "sorted_" + uploaded_file.name
            with open(sorted_csv_filename, 'w', newline='', encoding='utf-8') as csv_file:
                fieldnames = dataset[0].keys()
                csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                csv_writer.writeheader()
                csv_writer.writerows(sorted_multithreaded_dataset)

            return render(request, 'merge_sort_app/success.html', {
                'regular_execution_time': regular_execution_time_ns,
                'space_complexity': space_complexity,
                 'multithreaded_execution_time': multithreaded_execution_time_ns,
                'space_complexity_multithreaded': space_complexity_multithreaded,
                'sorted_csv_filename': sorted_csv_filename,
            })

        else:
            return render(request, 'merge_sort_app/upload.html', {'error_message': 'Please upload a CSV file.'})

    return render(request, 'merge_sort_app/upload.html')

def download_sorted_csv(request, file_name):
    file_path = os.path.join(settings.BASE_DIR, file_name)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as csv_file:
            response = HttpResponse(csv_file.read(), content_type='text/csv')  # Set the content type
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
    else:
        # Handle the case when the file doesn't exist
        return HttpResponse("File not found", status=404)