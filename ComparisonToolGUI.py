import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import csv
import os
import hashlib
import uuid
from datetime import datetime
import getpass
import difflib
import tempfile

# ------------------- Core Functions (Folder Comparison) ------------------- #

def compute_checksum(file_path):
    """
    Compute the SHA-256 checksum of a file.
    """
    hash_md5 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_mac_address():
    """
    Get the MAC address of the computer.
    """
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                    for elements in range(0, 2 * 6, 2)][::-1])
    return mac

def get_file_delimiter(file_path):
    """
    Determine file delimiter based on file extension.
    """
    if file_path.endswith('.txt'):
        return '|'
    elif file_path.endswith('.csv'):
        return ','
    else:
        raise ValueError(f"Unsupported file format: {file_path}. Only .txt and .csv are supported.")

def generate_row_hash(row):
    """
    Generate a hash for a row after normalizing whitespace.
    """
    normalized_row = [cell.strip() for cell in row]
    return hashlib.md5("|".join(normalized_row).encode('utf-8')).hexdigest()

def generate_overall_summary(pre_folder, post_folder, output_folder, comparison_results):
    """
    Generate an overall summary report as an HTML file.
    """
    pre_files = {f for f in os.listdir(pre_folder) if os.path.isfile(os.path.join(pre_folder, f))}
    post_files = {f for f in os.listdir(post_folder) if os.path.isfile(os.path.join(post_folder, f))}
    matching_files = pre_files & post_files
    pre_only_files = pre_files - post_files
    post_only_files = post_files - pre_files

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    overall_report_path = os.path.join(output_folder, f"Overall_Summary_{timestamp}.html")

    with open(overall_report_path, 'w', encoding='utf-8') as output_file:
        output_file.write("""
<html>
<head>
    <title>Overall Comparison Summary</title>
    <style>
        body { font-family: 'Segoe UI', Verdana, sans-serif; margin: 20px; }
        h1, h2 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; text-align: left; padding: 8px; }
        th { background-color: #f4f4f4; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        tr:hover { background-color: #f1f1f1; }
        .error { color: red; font-weight: bold; }
    </style>
</head>
<body>
""")
        output_file.write("<h1>Overall Comparison Summary</h1>")
        output_file.write("<h2>Summary Details</h2>")
        output_file.write("<table>")
        output_file.write("<tr><th>Metric</th><th>Value</th></tr>")
        output_file.write(f"<tr><td>Total Files in Pre Folder</td><td>{len(pre_files)}</td></tr>")
        output_file.write(f"<tr><td>Total Files in Post Folder</td><td>{len(post_files)}</td></tr>")
        output_file.write(f"<tr><td>Matching Files</td><td>{len(matching_files)}</td></tr>")
        output_file.write(f"<tr><td>Files Only in Pre</td><td>{len(pre_only_files)}</td></tr>")
        output_file.write(f"<tr><td>Files Only in Post</td><td>{len(post_only_files)}</td></tr>")
        output_file.write("</table>")
        if pre_only_files:
            output_file.write("<h2>Files Only in Pre Folder</h2><ul>")
            for file in sorted(pre_only_files):
                output_file.write(f"<li>{file}</li>")
            output_file.write("</ul>")
        if post_only_files:
            output_file.write("<h2>Files Only in Post Folder</h2><ul>")
            for file in sorted(post_only_files):
                output_file.write(f"<li>{file}</li>")
            output_file.write("</ul>")
        output_file.write("<h2>Matching Files</h2>")
        if matching_files:
            output_file.write("<table>")
            output_file.write("<tr><th>File Name</th><th>Status</th></tr>")
            for file in sorted(matching_files):
                status = "Comparison Completed" if file in comparison_results else "Comparison Skipped"
                output_file.write(f"<tr><td>{file}</td><td>{status}</td></tr>")
            output_file.write("</table>")
        else:
            output_file.write("<p>No matching files found.</p>")
        output_file.write("</body></html>")
    log_message(f"Overall summary written to: {overall_report_path}\n", 0)

def write_html_report(file_name, pre_file, post_file, result, execution_details, output_file_path, error_message=None):
    """
    Write the detailed comparison report as an HTML file.
    """
    pre_delimiter = get_file_delimiter(pre_file)
    post_delimiter = get_file_delimiter(post_file)
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write("""
<html>
<head>
    <title>Comparison Report</title>
    <style>
        body { font-family: 'Segoe UI', verdana, sans-serif; margin: 20px; }
        h1, h2 { color: #333; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 20px; }
        th, td { border: 1px solid #ddd; text-align: left; padding: 8px; }
        th { background-color: #f4f4f4; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        tr:hover { background-color: #f1f1f1; }
        .error { color: red; font-weight: bold; }
        img { max-width: 100%; margin-top: 20px; }
    </style>
</head>
<body>
""")
        output_file.write(f"<h1>Comparison Report for {os.path.splitext(os.path.basename(file_name))[0]}</h1>")
        output_file.write("<h2>Execution Details</h2>")
        output_file.write("""
<table>
    <tr><th>Detail</th><th>Value</th></tr>
""")
        output_file.write(f"<tr><td>Executor Name</td><td>{execution_details['executor_name']}</td></tr>")
        output_file.write(f"<tr><td>Start Time</td><td>{execution_details['start_time']}</td></tr>")
        output_file.write(f"<tr><td>End Time</td><td>{execution_details['end_time']}</td></tr>")
        output_file.write(f"<tr><td>Time Taken</td><td>{execution_details['time_taken']}</td></tr>")
        output_file.write(f"<tr><td>Pre File Path</td><td>{pre_file}</td></tr>")
        output_file.write(f"<tr><td>Post File Path</td><td>{post_file}</td></tr>")
        output_file.write(f"<tr><td>Pre File Checksum</td><td>{execution_details['pre_file_checksum']}</td></tr>")
        output_file.write(f"<tr><td>Post File Checksum</td><td>{execution_details['post_file_checksum']}</td></tr>")
        output_file.write(f"<tr><td>MAC Address</td><td>{execution_details['mac_address']}</td></tr>")
        output_file.write("</table>")
        output_file.write("<h2>Summary</h2>")
        if not error_message:
            output_file.write("""
<table>
    <tr><th>Metric</th><th>Value</th></tr>
""")
            output_file.write(f"<tr><td>Total rows in Pre</td><td>{result['total_pre_rows']}</td></tr>")
            output_file.write(f"<tr><td>Total rows in Post</td><td>{result['total_post_rows']}</td></tr>")
            output_file.write(f"<tr><td>Matching rows</td><td>{result['matching_rows']}</td></tr>")
            output_file.write(f"<tr><td>Total Different Rows</td><td>{result['total_different_rows']}</td></tr>")
            output_file.write(f"<tr><td>Total Pre-Only Rows</td><td>{len(open(result['pre_only_file']).readlines())}</td></tr>")
            output_file.write(f"<tr><td>Total Post-Only Rows</td><td>{len(open(result['post_only_file']).readlines())}</td></tr>")
            output_file.write("</table>")
            if result["no_differences"]:
                output_file.write("<h2>Result of Comparison</h2>")
                output_file.write("<p><strong>Both files are matching completely.</strong></p>")
            elif result["total_different_rows"] == 0:
                output_file.write("<h2>Result of Comparison</h2>")
                output_file.write("<p><strong>No differences for the matching rows. But there are differences in row counts.</strong></p>")
        else:
            output_file.write("<p class='error'>Summary could not be generated due to an error.</p>")
        if not error_message:
            output_file.write(f"<h2>Rows Only in Pre - {len(open(result['pre_only_file']).readlines())}</h2>")
            output_file.write("<table>")
            output_file.write("<tr>")
            for column in result["pre_header"]:
                output_file.write(f"<th>{column}</th>")
            output_file.write("</tr>")
            with open(result["pre_only_file"], 'r', encoding='utf-8') as pre_only_file:
                for line in pre_only_file:
                    output_file.write("<tr>")
                    for cell in line.strip().split(pre_delimiter):
                        output_file.write(f"<td>{cell}</td>")
                    output_file.write("</tr>")
            output_file.write("</table>")
        if not error_message:
            output_file.write(f"<h2>Rows Only in Post - {len(open(result['post_only_file']).readlines())}</h2>")
            output_file.write("<table>")
            output_file.write("<tr>")
            for column in result["post_header"]:
                output_file.write(f"<th>{column}</th>")
            output_file.write("</tr>")
            with open(result["post_only_file"], 'r', encoding='utf-8') as post_only_file:
                for line in post_only_file:
                    output_file.write("<tr>")
                    for cell in line.strip().split(post_delimiter):
                        output_file.write(f"<td>{cell}</td>")
                    output_file.write("</tr>")
            output_file.write("</table>")
        output_file.write("</body></html>")

def compare_large_files(pre_file, post_file):
    """
    Compare two large files by streaming them line by line using hash-based comparison.
    """
    pre_hashes = set()
    post_hashes = set()
    pre_delimiter = get_file_delimiter(pre_file)
    post_delimiter = get_file_delimiter(post_file)
    pre_only_file = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='', encoding='utf-8')
    post_only_file = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='', encoding='utf-8')
    with open(pre_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=pre_delimiter)
        pre_header = next(reader, None)
        for row in reader:
            row_hash = generate_row_hash(row)
            pre_hashes.add(row_hash)
    with open(post_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=post_delimiter)
        post_header = next(reader, None)
        for row in reader:
            row_hash = generate_row_hash(row)
            post_hashes.add(row_hash)
    pre_only_hashes = pre_hashes - post_hashes
    post_only_hashes = post_hashes - pre_hashes
    with open(pre_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=pre_delimiter)
        next(reader, None)
        for row in reader:
            if generate_row_hash(row) in pre_only_hashes:
                pre_only_file.write(pre_delimiter.join(row) + "\n")
    with open(post_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=post_delimiter)
        next(reader, None)
        for row in reader:
            if generate_row_hash(row) in post_only_hashes:
                post_only_file.write(post_delimiter.join(row) + "\n")
    pre_only_file.close()
    post_only_file.close()
    return {
        "pre_header": pre_header,
        "post_header": post_header,
        "total_pre_rows": len(pre_hashes),
        "total_post_rows": len(post_hashes),
        "matching_rows": len(pre_hashes & post_hashes),
        "total_different_rows": len(pre_only_hashes) + len(post_only_hashes),
        "pre_only_file": pre_only_file.name,
        "post_only_file": post_only_file.name,
        "no_differences": len(pre_only_hashes) == 0 and len(post_only_hashes) == 0
    }

def compare_folders(pre_folder, post_folder, output_folder):
    """
    Compare all common files in two folders and generate an HTML report for each.
    An overall summary is also generated.
    """
    pre_files = {f for f in os.listdir(pre_folder) if os.path.isfile(os.path.join(pre_folder, f))}
    post_files = {f for f in os.listdir(post_folder) if os.path.isfile(os.path.join(post_folder, f))}
    common_files = pre_files & post_files

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    comparison_results = {}

    for file_name in common_files:
        pre_file_path = os.path.join(pre_folder, file_name)
        post_file_path = os.path.join(post_folder, file_name)
        try:
            start_time = datetime.now()
            execution_details = {
                "executor_name": os.getlogin(),
                "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S'),
                "pre_file_checksum": compute_checksum(pre_file_path),
                "post_file_checksum": compute_checksum(post_file_path),
                "mac_address": get_mac_address(),
            }
            result = compare_large_files(pre_file_path, post_file_path)
            error_message = None
            end_time = datetime.now()
            execution_details["end_time"] = end_time.strftime('%Y-%m-%d %H:%M:%S')
            execution_details["time_taken"] = str(end_time - start_time)
            comparison_results[file_name] = True
        except Exception as e:
            result = {}
            error_message = f"An error occurred: {str(e)}"
            execution_details["end_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            execution_details["time_taken"] = "N/A"
            comparison_results[file_name] = False

        output_file_name = f"FolderComp_{os.path.splitext(os.path.basename(file_name))[0]}_{timestamp}.html"
        output_file_path = os.path.join(output_folder, output_file_name)
        write_html_report(file_name, pre_file_path, post_file_path, result, execution_details, output_file_path, error_message)
        log_message(f"Comparison result written to: {output_file_path}",0)

    generate_overall_summary(pre_folder, post_folder, output_folder, comparison_results)

# ------------------- File Comparison ------------------- #

# Function to compute file checksum
# def compute_checksum(file_path, hash_type="sha256"):
#     hash_func = hashlib.new(hash_type)
#     with open(file_path, "rb") as file:
#         while chunk := file.read(8192):
#             hash_func.update(chunk)
#     return hash_func.hexdigest()

# Function to compute a hash for a row
def compute_row_hash(row):
    row_str = '|'.join(row).encode('utf-8')
    return hashlib.sha256(row_str).hexdigest()

# Generator to read rows from a file and compute their hashes
def file_generator(file_path, delimiter, primary_key_cols):
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=delimiter)
        header = next(reader)  # Read the header
        for row in reader:
            if len(row) > max(primary_key_cols):
                key = tuple(row[i].strip() for i in primary_key_cols)  # Use tuple for hashability
                row_hash = compute_row_hash(row)
                yield key, row, row_hash, header

# Function to sort a file by primary key and write to a temporary file
def sort_file_to_temp(file_path, delimiter, primary_key_cols):
    temp_file = tempfile.NamedTemporaryFile(mode='w+', delete=False, encoding='utf-8')
    data = []
    for key, row, row_hash, header in file_generator(file_path, delimiter, primary_key_cols):
        data.append((key, row, row_hash))
    # Sort by primary key
    data.sort(key=lambda x: x[0])
    # Write sorted data to temporary file
    for key, row, row_hash in data:
        temp_file.write(f"{'|'.join(key)}\t{','.join(row)}\t{row_hash}\n")
    temp_file.close()
    return temp_file.name

# Function to compare two sorted files line by line
def compare_sorted_files(pre_temp_file, post_temp_file, primary_key_cols):
    differences = []
    fully_matching_rows = 0
    matching_data = []
    pre_only_rows = []
    post_only_rows = []

    # Get total lines for progress tracking
    total_lines = sum(1 for _ in open(pre_temp_file, 'r', encoding='utf-8')) + sum(1 for _ in open(post_temp_file, 'r', encoding='utf-8'))
    processed_lines = 0

    with open(pre_temp_file, 'r', encoding='utf-8') as pre_file, open(post_temp_file, 'r', encoding='utf-8') as post_file:
        pre_line = pre_file.readline()
        post_line = post_file.readline()
        while pre_line or post_line:
            pre_key = pre_line.split('\t')[0] if pre_line else None
            post_key = post_line.split('\t')[0] if post_line else None

            if pre_key == post_key:
                # Rows match, compare hashes
                pre_row = pre_line.split('\t')[1].split(',')
                post_row = post_line.split('\t')[1].split(',')
                pre_hash = pre_line.split('\t')[2].strip()
                post_hash = post_line.split('\t')[2].strip()

                if pre_hash == post_hash:
                    fully_matching_rows += 1
                    matching_data.append({"primary_key": pre_key, "pre_row": pre_row, "post_row": post_row})
                else:
                    # Hashes differ, perform detailed comparison
                    row_diff = []
                    for i in range(len(pre_row)):
                        if pre_row[i].strip() != post_row[i].strip() and i not in primary_key_cols:
                            row_diff.append({
                                "column_name": f"Column {i}",
                                "pre_value": pre_row[i],
                                "post_value": post_row[i]
                            })
                    if row_diff:
                        differences.append({
                            "primary_key": pre_key,
                            "differences": row_diff
                        })
                pre_line = pre_file.readline()
                post_line = post_file.readline()
            elif pre_key < post_key or post_key is None:
                # Row only in pre file
                pre_only_rows.append((pre_key, pre_line.split('\t')[1].split(',')))
                pre_line = pre_file.readline()
            else:
                # Row only in post file
                post_only_rows.append((post_key, post_line.split('\t')[1].split(',')))
                post_line = post_file.readline()

            # Update progress
            processed_lines += 1
            if processed_lines % 1000000 == 0:  # Print progress every 1 million lines
                log_message(f"Processed {processed_lines} of {total_lines} lines...\n", 1)

    summary = {
        "total_pre_rows": sum(1 for _ in open(pre_temp_file, 'r', encoding='utf-8')),
        "total_post_rows": sum(1 for _ in open(post_temp_file, 'r', encoding='utf-8')),
        "fully_matching_rows": fully_matching_rows,
        "pre_only_rows": len(pre_only_rows),
        "post_only_rows": len(post_only_rows),
        "differences": differences,
        "pre_only_data": {key: row for key, row in pre_only_rows},
        "post_only_data": {key: row for key, row in post_only_rows},
        "errors": [],
        "matching_data": matching_data
    }
    return summary

# Function to highlight differences
def highlight_differences(pre_value, post_value):
    highlighted_pre = []
    highlighted_post = []
    diff = difflib.ndiff(pre_value, post_value)
    for char in diff:
        if char.startswith("- "):
            highlighted_pre.append(f"<span style='background-color: #ff0000'>{char[2]}</span>")
        elif char.startswith("+ "):
            highlighted_post.append(f"<span style='background-color: #ff0000'>{char[2]}</span>")
        elif char.startswith(" "):
            highlighted_pre.append(char[2])
            highlighted_post.append(char[2])
    return "".join(highlighted_pre), "".join(highlighted_post)

# Function to generate the HTML report
def generate_html_report(pre_file, post_file, result, output_file_path, execution_details):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_name = getpass.getuser()
    pre_checksum = compute_checksum(pre_file)
    post_checksum = compute_checksum(post_file)
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(f"<html><head><title>Comparison Report - {os.path.splitext(os.path.basename(pre_file))[0]}</title>\n")
        output_file.write(f"<style>\n")
        output_file.write(f"body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}\n")
        output_file.write(f"table {{ width: 100%; border-collapse: collapse; width: 100%; margin-bottom: 20px; }}\n")
        output_file.write(f"table, th, td {{ border: 1px solid black; padding: 8px; text-align: left; }}\n")
        output_file.write(f"th {{ background-color: #f2f2f2; }}\n")
        output_file.write(f".pre_diff {{ background-color: #e3f2fd; }}\n")
        output_file.write(f".post_diff {{ background-color: #ffe0b2; }}\n")
        output_file.write(f".error {{ color: red; font-weight: bold; }}\n")
        output_file.write(f"</style></head><body>\n")
        output_file.write(f"<h1>Comparison Report - {os.path.splitext(os.path.basename(pre_file))[0]}</h1>\n")
        output_file.write("<h2>Execution Details</h2>")
        output_file.write("<table>\n")
        output_file.write("<tr><th>Detail</th><th>Value</th></tr>\n")
        output_file.write(f"<tr><td>Executor Name</td><td>{execution_details['executor_name']}</td></tr>\n")
        output_file.write(f"<tr><td>Start Time</td><td>{execution_details['start_time']}</td></tr>\n")
        output_file.write(f"<tr><td>End Time</td><td>{execution_details['end_time']}</td></tr>\n")
        output_file.write(f"<tr><td>Time Taken</td><td>{execution_details['time_taken']}</td></tr>\n")
        output_file.write(f"<tr><td>Pre File Path</td><td>{pre_file}</td></tr>\n")
        output_file.write(f"<tr><td>Pre File Checksum</td><td>{execution_details['pre_file_checksum']}</td></tr>\n")
        output_file.write(f"<tr><td>Post File Path</td><td>{post_file}</td></tr>\n")
        output_file.write(f"<tr><td>Post File Checksum</td><td>{execution_details['post_file_checksum']}</td></tr>\n")
        output_file.write(f"<tr><td>MAC Address</td><td>{execution_details['mac_address']}</td></tr>\n")
        output_file.write("</table>\n")

        total_differences = len(result["differences"])
        total_row_pre = result["total_pre_rows"]
        percent_diff = format((total_differences / total_row_pre), ".4%")
        total_errors = len(result["errors"])
        output_file.write("<h2>Summary</h2>\n")
        output_file.write("<table>\n")
        output_file.write("<tr><th>Metric</th><th>Count</th></tr>\n")
        output_file.write(f"<tr><td>Total rows in Pre</td><td>{result['total_pre_rows']}</td></tr>\n")
        output_file.write(f"<tr><td>Total rows in Post</td><td>{result['total_post_rows']}</td></tr>\n")
        output_file.write(f"<tr><td>Matching rows</td><td>{result['fully_matching_rows']}</td></tr>\n")
        output_file.write(f"<tr><td>Rows only in Pre</td><td>{result['pre_only_rows']}</td></tr>\n")
        output_file.write(f"<tr><td>Rows only in Post</td><td>{result['post_only_rows']}</td></tr>\n")
        output_file.write(f"<tr><td>Total rows with differences</td><td>{total_differences}</td></tr>\n")
        output_file.write(f"<tr><td>Total errors</td><td>{total_errors}</td></tr>\n")
        output_file.write("</table>\n")

        if total_differences > 0:
            output_file.write("<h2>Result of Comparison</h2>\n")
            output_file.write("<p>There are differences</p>\n")
            output_file.write(f"<h2>Differences Table - {total_differences} - {percent_diff}</h2>\n")
            output_file.write("<table>\n")
            output_file.write("<tr><th>Composite Key</th><th>Field Name</th><th>Pre Value</th><th>Post Value</th></tr>\n")
            for diff in result["differences"]:
                composite_key = diff["primary_key"]
                for col_diff in diff["differences"]:
                    highlighted_pre, highlighted_post = highlight_differences(col_diff['pre_value'], col_diff['post_value'])
                    output_file.write("<tr>\n")
                    output_file.write(f"<td>{composite_key}</td>\n")
                    output_file.write(f"<td>{col_diff['column_name']}</td>\n")
                    output_file.write(f"<td class='pre_diff'>{highlighted_pre}</td>\n")
                    output_file.write(f"<td class='post_diff'>{highlighted_post}</td>\n")
                    output_file.write("</tr>\n")
            output_file.write("</table>\n")
        else:
            output_file.write("<h2>Result of Comparison</h2>\n")
            output_file.write("<p>Both the files are complete match !!</p>\n")

        if result["pre_only_data"]:
            output_file.write("<h2>Rows only in Pre</h2>\n<ul>\n")
            for key, row in result["pre_only_data"].items():
                output_file.write(f"<li><b>Primary Key:</b> {key} <b>Row Data:</b> {row}</li>\n")
            output_file.write("</ul>\n")

        if result["post_only_data"]:
            output_file.write("<h2>Rows only in Post</h2>\n<ul>\n")
            for key, row in result["post_only_data"].items():
                output_file.write(f"<li><b>Primary Key:</b> {key} <b>Row Data:</b> {row}</li>\n")
            output_file.write("</ul>\n")

        output_file.write("</body></html>\n")

# def get_mac_address():
#     """
#     Get the MAC address of the computer.
#     """
#     return ':'.join(['{:02x}'.format((uuid.getnode()>> elements) & 0xff)
#                      for elements in range(0, 2 * 6, 2) ][ ::- 1])


# Main function to compare files and generate a report
def compare_files_and_generate_report(pre_file, post_file, primary_key_cols, output_folder):
    primary_key_cols = list(map(int, primary_key_cols.split(",")))
    start_time = datetime.now()
    execution_details = {
        "executor_name": os.getlogin(),
        "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S'),
        "pre_file_checksum": compute_checksum(pre_file),
        "post_file_checksum": compute_checksum(post_file),
        "mac_address": get_mac_address(),
    }

    # Sort files and write to temporary files
    log_message(f"Sorting pre file... {datetime.now()}\n",1)
    pre_temp_file = sort_file_to_temp(pre_file, get_file_delimiter(pre_file), primary_key_cols)
    log_message(f"Sorting post file... {datetime.now()}\n", 1)
    post_temp_file = sort_file_to_temp(post_file, get_file_delimiter(post_file), primary_key_cols)

    # Compare sorted files
    log_message(f"Comparing files... {datetime.now()}\n", 1)
    result = compare_sorted_files(pre_temp_file, post_temp_file, primary_key_cols)

    end_time = datetime.now()
    execution_details["end_time"] = end_time.strftime('%Y-%m-%d %H:%M:%S')
    execution_details["time_taken"] = str(end_time - start_time)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    summary_file_name = f"FileCompare_Report_{os.path.splitext(os.path.basename(pre_file))[0]}_{timestamp}.html"
    summary_file_path = os.path.join(output_folder, summary_file_name)
    log_message(f"Generate Report HTML.. {datetime.now()}\n", 1)
    generate_html_report(pre_file, post_file, result, summary_file_path, execution_details)
    log_message(f"Summary and differences report generated: {summary_file_path}\n", 1)

    # Clean up temporary files
    os.unlink(pre_temp_file)
    os.unlink(post_temp_file)

# ------------------- GUI Interface ------------------- #

def run_folder_comparison():
    pre_folder = entry_source_folder.get()
    post_folder = entry_target_folder.get()
    output_folder = entry_result_folder.get()
    if not pre_folder or not post_folder or not output_folder:
        messagebox.showerror("Error", "All fields must be filled!")
        return
    # Run comparison in a separate thread so the GUI stays responsive.
    threading.Thread(target=execute_compare, args=(pre_folder, post_folder, output_folder), daemon=True).start()

def execute_compare(pre_folder, post_folder, output_folder):
    try:
        log_message("Starting folder comparison...\n",0)
        compare_folders(pre_folder, post_folder, output_folder)
        log_message("Folder comparison completed.\n", 0)
        messagebox.showinfo("Success", "Folder comparison completed! Check the output folder.")
        save_history(pre_folder, post_folder, output_folder, "Folder Comparison")
        load_history()
    except Exception as e:
        log_message(f"Error: {str(e)}\n", 0)
        messagebox.showerror("Error", str(e))

def log_message(message, type):
    if type == 0:
        output_text.configure(state="normal")
        output_text.insert(tk.END, message)
        output_text.see(tk.END)
        output_text.configure(state="disabled")
    else:
        output_text1.configure(state="normal")
        output_text1.insert(tk.END, message)
        output_text1.see(tk.END)
        output_text1.configure(state="disabled")

def browse_file(entry):
    filename = filedialog.askopenfilename()
    if filename:
        entry.delete(0, tk.END)
        entry.insert(0, filename)

def browse_folder(entry):
    foldername = filedialog.askdirectory()
    if foldername:
        entry.delete(0, tk.END)
        entry.insert(0, foldername)

def run_file_comparison():
    log_message("Running Comparison Function\n",1)
    pre_file = entry_source.get()
    post_file = entry_target.get()
    primary_key_cols = entry_indexes.get()
    output_folder = entry_output.get()

    if not pre_file or not post_file or not primary_key_cols or not output_folder:
        messagebox.showerror("Error", "All fields must be filled!")
        return
    # Run comparison in a separate thread so the GUI stays responsive.
    threading.Thread(target=execute_file_comparison, args=(pre_file, post_file, primary_key_cols, output_folder), daemon=True).start()

def execute_file_comparison(pre_file, post_file, primary_key_cols, output_folder):
    try:
        log_message("Starting file comparison...\n", 1)
        compare_files_and_generate_report(pre_file, post_file, primary_key_cols, output_folder)
        log_message("File comparison completed.\n", 1)
        messagebox.showinfo("Success", "File comparison completed! Check the output folder.")
        save_history(pre_file, post_file, output_folder, "File Comparison")
        load_history()
    except Exception as e:
        log_message(f"Error: {str(e)}\n", 1)
        messagebox.showerror("Error", str(e))

def save_history(source, target, output, comparison_type):
    history_file = "comparison_history.txt"
    os.system(f"attrib +s +h {history_file}")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(history_file, "a") as file:
        file.write(f"{timestamp} | {comparison_type} | {source} | {target} | {output}\n")

def load_history():
    history_text.delete(1.0, tk.END)
    history_file = "comparison_history.txt"
    if os.path.exists(history_file):
        with open(history_file, "r") as file:
            history_text.insert(tk.END, file.read())

# GUI Setup
root = tk.Tk()
root.title("Comparison Tool")
root.geometry("600x600")
# root.iconbitmap("compare.ico")  # Set the window icon

notebook = ttk.Notebook(root)
frame_folder_comp = ttk.Frame(notebook)
frame_file_comp = ttk.Frame(notebook)
frame_history = ttk.Frame(notebook)
notebook.add(frame_folder_comp, text="Folder Comparison")
notebook.add(frame_file_comp, text="File Comparison")
notebook.add(frame_history, text="History")
notebook.pack(expand=True, fill="both")

# File Comparison Tab
frame_inputs = tk.Frame(frame_file_comp)
frame_inputs.pack(pady=10)

tk.Label(frame_inputs, text="Source File:").grid(row=0, column=0)
entry_source = tk.Entry(frame_inputs, width=50)
entry_source.grid(row=0, column=1)
tk.Button(frame_inputs, text="Browse", command=lambda: browse_file(entry_source)).grid(row=0, column=2)

tk.Label(frame_inputs, text="Target File:").grid(row=1, column=0)
entry_target = tk.Entry(frame_inputs, width=50)
entry_target.grid(row=1, column=1)
tk.Button(frame_inputs, text="Browse", command=lambda: browse_file(entry_target)).grid(row=1, column=2)

tk.Label(frame_inputs, text="Indexes:").grid(row=2, column=0)
entry_indexes = tk.Entry(frame_inputs, width=50)
entry_indexes.grid(row=2, column=1)

tk.Label(frame_inputs, text="Output Folder:").grid(row=3, column=0)
entry_output = tk.Entry(frame_inputs, width=50)
entry_output.grid(row=3, column=1)
tk.Button(frame_inputs, text="Browse", command=lambda: browse_folder(entry_output)).grid(row=3, column=2)

tk.Button(frame_file_comp, text="Compare Files", command=run_file_comparison).pack(pady=10)

# Output Textbox
output_text1 = scrolledtext.ScrolledText(frame_file_comp, height=10)
output_text1.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Folder Comparison Tab
frame_folder_inputs = tk.Frame(frame_folder_comp)
frame_folder_inputs.pack(pady=10)

tk.Label(frame_folder_inputs, text="Source Folder:").grid(row=0, column=0)
entry_source_folder = tk.Entry(frame_folder_inputs, width=50)
entry_source_folder.grid(row=0, column=1)
tk.Button(frame_folder_inputs, text="Browse", command=lambda: browse_folder(entry_source_folder)).grid(row=0, column=2)

tk.Label(frame_folder_inputs, text="Target Folder:").grid(row=1, column=0)
entry_target_folder = tk.Entry(frame_folder_inputs, width=50)
entry_target_folder.grid(row=1, column=1)
tk.Button(frame_folder_inputs, text="Browse", command=lambda: browse_folder(entry_target_folder)).grid(row=1, column=2)

tk.Label(frame_folder_inputs, text="Result Folder:").grid(row=2, column=0)
entry_result_folder = tk.Entry(frame_folder_inputs, width=50)
entry_result_folder.grid(row=2, column=1)
tk.Button(frame_folder_inputs, text="Browse", command=lambda: browse_folder(entry_result_folder)).grid(row=2, column=2)

tk.Button(frame_folder_comp, text="Compare Folders", command=run_folder_comparison).pack(pady=10)

# Output Textbox
output_text = scrolledtext.ScrolledText(frame_folder_comp, height=10)
output_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# History Tab
history_text = scrolledtext.ScrolledText(frame_history, height=20)
history_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
load_history()

if __name__ == "__main__":
    root.mainloop()
