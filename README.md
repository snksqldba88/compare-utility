# compare-utility
Compare two comma separated or pipe delimiter separated files and find the differnces. Used compare two tables, if the table is extracted as a flat file with either comma (,) or pipe (|) as row delimiter.

**Note**: The Script is created based on the assumption, the rows in the table are distinct, atleast one column or combination of few columns forms a primary key.

To use the FileCompare.py
-------------------------
1. Download the FileComparison.py
2. Use the python interpreter, pass the Source File, Target File, primary key or composite key (comma separated values), output folder as parameters.
3. The columns will be counted starting from 0. So, if the primary key column is 4th column, then pass 3 as primary column #.
4. The script will compare both the files and show the differences in a html file.
5. It will highlight the differences between source and target in the html file.
6. If there are no differences, it will post the result.

To use the FolderCompare.py
---------------------------
1. Download the FolderCompare.py
2. Use python interpreter, pass the Source Folder, Target Folder and Output folder.
3. Assuming both folders having identically named files with tabular structure.
4. It assumes whole file as a single columned table and consider each row as a value in the table and each value is distinct.
5. It will show differences as Pre-only rows and Post-only rows. 

To use the GUI Version 
----------------------
1. Download the ComparisonToolGUI.py script
2. Use the python interpreter to run the file.
3. Choose the tool which is needed - Folder Comparison Tab for Folder Comparison or File Comparison for File Comparison.
4. Folder Comparison - It compares two folders with identical files for comparison. Assuming both folders are having identical named files.
5. File Comparison - It compares two files with similar tabular structure. Assuming two tables with a primary key column or multiple columns making a composite primary key.
6. Output will be saved in the output folder.

![image](https://github.com/user-attachments/assets/c1f649d8-c93c-42d0-8490-3765aa89e233)

![image](https://github.com/user-attachments/assets/14d64bc4-a306-41c8-b437-7ef8b2c647c3)
