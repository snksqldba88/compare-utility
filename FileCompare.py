import csv
import os
import hashlib
import uuid
from datetime import datetime
import argparse
import getpass
import difflib
import tempfile
from itertools import zip_longest

# Function to compute file checksum
def compute_checksum(file_path, hash_type="sha256"):
    hash_func = hashlib.new(hash_type)
    with open(file_path, "rb") as file:
        while chunk := file.read(8192):
            hash_func.update(chunk)
    return hash_func.hexdigest()

# Function to determine delimiter based on file extension
def determine_delimiter(file_path):
    if file_path.endswith(".txt"):
        return '|'
    elif file_path.endswith(".csv"):
        return ','
    else:
        raise ValueError(f"Unsupported file format for: {file_path}")

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
                print(f"Processed {processed_lines} of {total_lines} lines...")

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

def get_mac_address():
    """
    Get the MAC address of the computer.
    """
    return ':'.join(['{:02x}'.format((uuid.getnode()>> elements) & 0xff)
                     for elements in range(0, 2 * 6, 2) ][ ::- 1])


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
    print(f"Sorting pre file... {datetime.now()}")
    pre_temp_file = sort_file_to_temp(pre_file, determine_delimiter(pre_file), primary_key_cols)
    print(f"Sorting post file... {datetime.now()}")
    post_temp_file = sort_file_to_temp(post_file, determine_delimiter(post_file), primary_key_cols)

    # Compare sorted files
    print(f"Comparing files... {datetime.now()}")
    result = compare_sorted_files(pre_temp_file, post_temp_file, primary_key_cols)

    end_time = datetime.now()
    execution_details["end_time"] = end_time.strftime('%Y-%m-%d %H:%M:%S')
    execution_details["time_taken"] = str(end_time - start_time)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    summary_file_name = f"FileCompare_Report_{os.path.splitext(os.path.basename(pre_file))[0]}_{timestamp}.html"
    summary_file_path = os.path.join(output_folder, summary_file_name)
    print(f"Generate Report HTML.. {datetime.now()}")
    generate_html_report(pre_file, post_file, result, summary_file_path, execution_details)
    print(f"Summary and differences report generated: {summary_file_path}")

    # Clean up temporary files
    os.unlink(pre_temp_file)
    os.unlink(post_temp_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compare two files and generate an HTML report.")
    parser.add_argument("pre_file", type=str, help="The pre file to compare")
    parser.add_argument("post_file", type=str, help="The post file to compare")
    parser.add_argument("primary_key_cols", type=str, help="Comma-separated indices of the composite key columns (e.g., 0,1)")
    parser.add_argument("output_folder", type=str, help="The folder to save the report")
    args = parser.parse_args()
    print(f"The Script is starting.. {datetime.now()}")
    compare_files_and_generate_report(args.pre_file, args.post_file, args.primary_key_cols, args.output_folder)
