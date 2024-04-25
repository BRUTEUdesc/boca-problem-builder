#!/usr/bin/env python3
import glob
import os
import json
import shutil
import subprocess
import sys
from pathlib import Path
import main

def read_contest_file(directory):
    """Reads the contest configuration from a JSON file."""
    file_path = Path(directory) / "contest.json"
    if not file_path.exists():
        sys.exit(f"{file_path} not found")
    with open(file_path, 'r') as file:
        return json.load(file)

def find_polygon_package(directory, problem):
    """Finds the polygon package file based on problem configuration."""
    if problem["POLYGON_PACKAGE"] == "DEFAULT":
        pattern = f'{directory}/{problem["PROBLEM_LETTER"].lower()}*'
        file_list = [f for f in glob.glob(pattern) if not f.endswith(".json")]
        if not file_list:
            print(f"No file found for problem {problem['PROBLEM_LETTER']}, skipping...")
            return None
        if len(file_list) > 1:
            print(f"More than one file found for problem {problem['PROBLEM_LETTER']}, skipping...")
            return None
        return file_list[0]
    return problem["POLYGON_PACKAGE"]

def run_main_script(problem, directory):
    """Executes the main.py script for a given problem."""
    file_name = find_polygon_package(directory, problem)
    if not file_name:
        return
    command = ["python3", "main.py", problem["PROBLEM_LETTER"], file_name]
    command.extend(str(problem[f"{lang}_TL_FACTOR"]) for lang in ("JAVA", "PYTHON") if f"{lang}_TL_FACTOR" in problem)
    subprocess.run(command)

def clean_folders():
    """Cleans and backs up the directories before the contest setup."""
    packages_folder = Path("packages")
    zip_folder = Path("zip_packages")
    if zip_folder.exists():
        shutil.rmtree(zip_folder)
    backup_base = Path("backups")
    backup_base.mkdir(exist_ok=True)

    if packages_folder.exists():
        for folder_path in packages_folder.iterdir():
            if folder_path.is_dir():  # Make sure it's a directory
                problem_idx = folder_path.name.split('_')[-1]
                # Call the backup function from main
                main.backup(str(folder_path), str(backup_base), problem_idx)
                shutil.rmtree(folder_path)

if __name__ == "__main__":
    main.check_run_directory()
    if len(sys.argv) < 2:
        sys.exit("Usage: python3 make_contest.py {CONTEST DIRECTORY}")
    contest_directory = sys.argv[1]
    if not os.path.exists(contest_directory):
        sys.exit(f"The directory {contest_directory} does not exist")
    print("Backing up any existing packages")
    clean_folders()
    problems = read_contest_file(contest_directory)
    for problem in problems:
        run_main_script(problem, contest_directory)
