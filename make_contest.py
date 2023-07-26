#!/usr/bin/env python3
import glob
import os
import json
import shutil
import subprocess
import sys
from distutils.dir_util import copy_tree


def read_contest_file(directory):
    file_path = os.path.join(directory, "contest.json")
    if not os.path.exists(file_path):
        print(file_path, "not found")
        exit(1)
    with open(file_path, 'r') as file:
        problems = json.load(file)
    return problems


def run_main_script(problem, directory):
    if problem["POLYGON_PACKAGE"] == "DEFAULT":
        # Find the first file in the polygon_contest_packages directory that starts with the problem letter
        file_list = glob.glob(directory + '/' + problem["PROBLEM LETTER"].lower() + '*')
        if not file_list:
            print("No file found for problem", problem["PROBLEM LETTER"])
            return
        file_name = file_list[0]  # Use the first matching file
    else:
        file_name = problem["POLYGON_PACKAGE"]
    command = ["python3", "main.py", problem["PROBLEM LETTER"], file_name]
    if "JAVA_TL_FACTOR" in problem:
        command.append(str(problem["JAVA_TL_FACTOR"]))
    if "PYTHON_TL_FACTOR" in problem:
        command.append(str(problem["PYTHON_TL_FACTOR"]))
    subprocess.run(command)


def clean_folders():
    folders = ["packages", "zip_packages"]
    for folder in folders:
        if os.path.exists(folder):
            backup_number = 1
            backup_folder = 'backup/' + folder + '-' + str(backup_number)
            while os.path.isdir(backup_folder):
                backup_number += 1
                backup_folder = 'backup/' + folder + '-' + str(backup_number)
            copy_tree(folder, backup_folder)
            shutil.rmtree(folder)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 make_contest.py {CONTEST DIRECTORY}")
        exit(1)
    contest_directory = sys.argv[1]
    if not os.path.exists(contest_directory):
        print("The directory", contest_directory, "does not exist")
        exit(1)
    print("Backuping any existing packages")
    clean_folders()
    problems = read_contest_file(contest_directory)
    for problem in problems:
        run_main_script(problem, contest_directory)
