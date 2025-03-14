import os
import csv
import sys
import hashlib
# import pyautogui
import uuid
from datetime import datetime
import tempfile


def compute_checksum(file_path):
    """
    Compute the MD5 checksum of a file.
    """
    hash_md5 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


# def capture_screenshot(output_folder, file_name):
#     """
#     Capture a screenshot of the current screen and save it as a PNG file.
#     """
#     screenshot_path = os.path.join(output_folder, f"{file_name}_screenshot.png")
#     screenshot = pyautogui.screenshot()
#     screenshot.save(screenshot_path)
#     return screenshot_path


def get_mac_address():
    """
    Get the MAC address of the computer.
    """
    mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) for elements in range(0, 2 * 6, 2)][::-1])
    return mac

def get_file_delimiter(file_path):
    """
    Determine the file delimiter based on the file extension.
    """
    if file_path.endswith('.txt'):
        return '|'
    elif file_path.endswith('.csv'):
        return ','
    else:
        raise ValueError(f"Unsupported file format: {file_path}. Only .txt and .csv are supported.")


def generate_row_hash(row):
    """
    Generate a hash for a row after normalizing (trimming whitespace).
    """
    normalized_row = [cell.strip() for cell in row]  # Remove leading/trailing spaces
    return hashlib.md5("|".join(normalized_row).encode('utf-8')).hexdigest()

def generate_overall_summary(pre_folder, post_folder, output_folder, comparison_results):
    """
    Generate an overall summary report of the comparison process.
    Tracks:
      - Total files in pre and post folders.
      - Number of matching files.
      - Files missing in either pre or post folders.
    """
    # Get the list of files
    pre_files = {f for f in os.listdir(pre_folder) if os.path.isfile(os.path.join(pre_folder, f))}
    post_files = {f for f in os.listdir(post_folder) if os.path.isfile(os.path.join(post_folder, f))}

    # Determine matches and mismatches
    matching_files = pre_files & post_files
    pre_only_files = pre_files - post_files
    post_only_files = post_files - pre_files

    # Generate the overall summary HTML report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    overall_report_path = os.path.join(output_folder, f"Overall_Summary_{timestamp}.html")

    with open(overall_report_path, 'w', encoding='utf-8') as output_file:
        # HTML Header
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

        # Title
        output_file.write("<h1>Overall Comparison Summary</h1>")

        # Summary Details Table
        output_file.write("<h2>Summary Details</h2>")
        output_file.write("<table>")
        output_file.write("<tr><th>Metric</th><th>Value</th></tr>")
        output_file.write(f"<tr><td>Total Files in Pre Folder</td><td>{len(pre_files)}</td></tr>")
        output_file.write(f"<tr><td>Total Files in Post Folder</td><td>{len(post_files)}</td></tr>")
        output_file.write(f"<tr><td>Matching Files</td><td>{len(matching_files)}</td></tr>")
        output_file.write(f"<tr><td>Files Only in Pre</td><td>{len(pre_only_files)}</td></tr>")
        output_file.write(f"<tr><td>Files Only in Post</td><td>{len(post_only_files)}</td></tr>")
        output_file.write("</table>")

        # Files Only in Pre Folder
        if pre_only_files:
            output_file.write("<h2>Files Only in Pre Folder</h2>")
            output_file.write("<ul>")
            for file in sorted(pre_only_files):
                output_file.write(f"<li>{file}</li>")
            output_file.write("</ul>")

        # Files Only in Post Folder
        if post_only_files:
            output_file.write("<h2>Files Only in Post Folder</h2>")
            output_file.write("<ul>")
            for file in sorted(post_only_files):
                output_file.write(f"<li>{file}</li>")
            output_file.write("</ul>")

        # Matching Files Summary
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

        # HTML Footer
        output_file.write("</body></html>")

    print(f"Overall summary written to: {overall_report_path}")

def write_html_report(file_name, pre_file, post_file, result, execution_details, output_file_path, error_message=None):
    """
    Write the comparison result and error information (if any) to an HTML file.
    """
    pre_delimiter = get_file_delimiter(pre_file)
    post_delimiter = get_file_delimiter(post_file)
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        # HTML Header with CSS Styling
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

        # Title
        output_file.write(f"<h1>Comparison Report for {os.path.splitext(os.path.basename(file_name))[0]}</h1>")

        # Execution Details Table
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

        # Embed Screenshot
        # if screenshot_path:
        #     output_file.write("<h2>Execution Screenshot</h2>")
        #     output_file.write(f"<img src='{screenshot_path}' alt='Execution Screenshot'>")

        # Summary Table
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

            # Add message for no differences
            if result["no_differences"]:
                output_file.write("<h2>Result of Comparison</h2>")
                output_file.write("<p><strong>Both files are matching completely.</strong></p>")
            elif result["total_different_rows"] == 0:
                output_file.write("<h2>Result of Comparison</h2>")
                output_file.write("<p><strong>No differences for the matching rows. But there are </strong></p>")

        else:
            output_file.write("<p class='error'>Summary could not be generated due to an error.</p>")

        # Pre-Only Rows
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

        # Post-Only Rows
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

        # HTML Footer
        output_file.write("</body></html>")

def compare_large_files(pre_file, post_file):
    """
    Compare two large files by streaming through them line by line.
    Uses hash-based comparison for efficiency and stores intermediate results in temporary files.
    """
    pre_hashes = set()
    post_hashes = set()

    # Determine delimiters for the files
    pre_delimiter = get_file_delimiter(pre_file)
    post_delimiter = get_file_delimiter(post_file)

    # Temporary files for storing unique rows
    pre_only_file = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='', encoding='utf-8')
    post_only_file = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='', encoding='utf-8')

    # Read Pre File
    with open(pre_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=pre_delimiter)
        pre_header = next(reader, None)  # Extract header
        for row in reader:
            row_hash = generate_row_hash(row)
            pre_hashes.add(row_hash)

    # Read Post File
    with open(post_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=post_delimiter)
        post_header = next(reader, None)  # Extract header
        for row in reader:
            row_hash = generate_row_hash(row)
            post_hashes.add(row_hash)

    # Compare and write results to temp files
    pre_only_hashes = pre_hashes - post_hashes
    post_only_hashes = post_hashes - pre_hashes

    # Write pre-only rows to temp file
    with open(pre_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=',')
        next(reader, None)  # Skip header
        for row in reader:
            if generate_row_hash(row) in pre_only_hashes:
                pre_only_file.write(pre_delimiter.join(row) + "\n")

    # Write post-only rows to temp file
    with open(post_file, 'r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter=',')
        next(reader, None)  # Skip header
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

# Update the compare_folders function to include the overall summary generation
def compare_folders(pre_folder, post_folder, output_folder):
    """
    Compare all common files in two folders and generate an HTML report for each.
    At the end, generate an overall summary of the comparison.
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

            # Capture Execution Details
            execution_details = {
                "executor_name": os.getlogin(),
                "start_time": start_time.strftime('%Y-%m-%d %H:%M:%S'),
                "pre_file_checksum": compute_checksum(pre_file_path),
                "post_file_checksum": compute_checksum(post_file_path),
                "mac_address": get_mac_address(),
            }

            # Perform File Comparison
            result = compare_large_files(pre_file_path, post_file_path)
            error_message = None
            end_time = datetime.now()
            execution_details["end_time"] = end_time.strftime('%Y-%m-%d %H:%M:%S')
            execution_details["time_taken"] = str(end_time - start_time)

            # Capture Screenshot
            # screenshot_path = capture_screenshot(output_folder, file_name)

            # Store result for overall summary
            comparison_results[file_name] = True

        except Exception as e:
            result = {}
            error_message = f"An error occurred: {str(e)}"
            execution_details["end_time"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            execution_details["time_taken"] = "N/A"
            # screenshot_path = None

            # Mark comparison as failed for this file
            comparison_results[file_name] = False

        # Generate HTML Report for the File
        output_file_name = f"FolderComp_{os.path.splitext(os.path.basename(file_name))[0]}_{timestamp}.html"
        output_file_path = os.path.join(output_folder, output_file_name)
        write_html_report(file_name, pre_file_path, post_file_path, result, execution_details, output_file_path, error_message)

        print(f"Comparison result written to: {output_file_path}")

    # Generate Overall Summary Report
    generate_overall_summary(pre_folder, post_folder, output_folder, comparison_results)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python compare_folders.py <pre_folder> <post_folder> <output_folder>")
        sys.exit(1)

    pre_folder = sys.argv[1]
    post_folder = sys.argv[2]
    output_folder = sys.argv[3]

    compare_folders(pre_folder, post_folder, output_folder)
