#!/usr/bin/env python3
from datetime import datetime

from math import gcd
from shutil import rmtree, copy, copytree, make_archive, which
import zipfile
import sys
import os
import xml.etree.ElementTree as eT


def ensure_dir_exists(directory):
    """
    Ensures that the specified directory exists.

    If the directory does not exist, it creates it, including any necessary parent directories.

    Args:
    directory (str): The path to the directory to check and ensure exists.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def clean_directory(directory):
    """
    Cleans the specified directory by removing it and recreating it.

    This function ensures that the directory is completely empty by deleting it first if it exists,
    and then recreating it.

    Args:
    directory (str): The path to the directory to clean.
    """
    if os.path.exists(directory):
        rmtree(directory)
    os.makedirs(directory)


def make_limits(limits_folder, repetitions, memory_limit, clang_timelimit, java_timelimit, python_timelimit):
    """
    Creates limit files for each language supported by the Maratona de Programação.

    Each file contains specific settings for the time limit, number of repetitions, and memory limit applicable to
    the programming language.

    Args: limits_folder (str): The path to the directory where the limits files will be created. repetitions (int):
    The number of repetitions each test case will be executed (and all repetitions should finish within the time
    limit). memory_limit (int): The maximum amount of memory each test case can use, specified in megabytes (MB).
    clang_timelimit (int): The time limit for languages processed by Clang (C and C++), specified in seconds.
    java_timelimit (int): The time limit for Java, specified in seconds. python_timelimit (int): The time limit for
    Python, specified in seconds.

    The function creates a file for each specified language, writing the limits according to the given constraints.
    """
    try:
        # Define time limits for each language or language group
        time_limits = {
            'c': clang_timelimit,
            'cpp': clang_timelimit,
            'java': java_timelimit,
            'kt': java_timelimit,
            'py3': python_timelimit
        }

        # Language extensions for the limits files
        limit_file_extensions = ['c', 'cpp', 'java', 'kt', 'py3']

        # Create and write limits to each file
        for ext in limit_file_extensions:
            file_path = os.path.join(limits_folder, ext)
            with open(file_path, 'w') as limit_file:
                timelimit = time_limits.get(ext, None)
                if timelimit is None:
                    raise ValueError(f"Unknown language extension: {ext}")

                # Write the limits
                limit_file.write(f"echo {timelimit}\n") # keeps the polygon timelimit
                limit_file.write(f"echo {repetitions}\n") # keeps the polygon timelimit
                limit_file.write(f"echo {memory_limit}\n")
                limit_file.write("echo 15360\n")
                limit_file.write("exit 0\n")
    except Exception as e:
        print("Error:", e)
        sys.exit(1)


def validate_arguments(args):
    """
    Validates command line arguments for a problem packaging script.

    Ensures the correct number of arguments, verifies the format of the problem index, checks file existence and type.

    Args:
    args (list of str): Command line arguments provided to the script.

    Returns:
    tuple: Contains the validated problem index, file name, and time limit factors for Java and Python.

    Errors are handled by raising exceptions for specific invalid conditions and printing error messages before exiting.
    """
    try:
        # Check minimum number of arguments
        if len(args) < 3:
            raise ValueError("Usage: python3 make_from_full_package.py PROBLEM_LETTER POLYGON_PACKAGE.zip [java_tl_factor] ["
                             "python_tl_factor]")

        problem_idx = args[1]
        file_name = args[2]

        # Default time limit factors
        java_tl_factor = 1 if len(args) < 4 else int(args[3])
        python_tl_factor = 1 if len(args) < 5 else int(args[4])

        # Validate problem index
        if not (problem_idx.isupper() and len(problem_idx) == 1):
            raise ValueError("The problem letter must be a capital letter and one character long.")

        # Check if the file exists
        if not os.path.exists(file_name):
            raise FileNotFoundError(f"The file {file_name} does not exist.")

        # Ensure the file is a zip file
        if not file_name.endswith('.zip'):
            raise ValueError("The file must be a zip file.")

        return problem_idx, file_name, java_tl_factor, python_tl_factor
    except Exception as e:
        print("Error:", e)
        sys.exit(1)


def unzip_and_check_polygon_package(zip_file, polygon_folder):
    """
    Extracts a polygon package from a ZIP file and checks for required files within the extracted contents.

    Args:
    zip_file (str): The path to the ZIP file containing the polygon package.
    polygon_folder (str): The directory where the ZIP file will be extracted to.

    This function checks for the existence of specific required files after extraction and raises an exception if any
    files are missing. This ensures the package's integrity and readiness for further processing.
    """
    required_files = [
        '/check.cpp',
        '/files/testlib.h',
        '/problem.xml',
        '/statements/.pdf/portuguese/problem.pdf'
    ]
    try:
        # Extract the ZIP file to the designated folder
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(polygon_folder)

        # Check for the existence of all required files in the extracted folder
        for file in required_files:
            if not os.path.exists(polygon_folder + file):
                raise Exception(f"Required file '{file}' not found in the ZIP package.")
    except zipfile.BadZipFile:
        print("Error: Bad ZIP file.")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: File", zip_file, "not found.")
        sys.exit(1)
    except Exception as e:
        print("Error:", e)
        sys.exit(1)


def backup(source, target, problem_idx):
    """
    Backs up the contents of a source directory to a target directory.

    This function creates a backup folder within the target directory, appending a timestamp to avoid collisions.
    If a backup with the same timestamp already exists (possible with quick successive backups), it appends an 
    increasing number to ensure uniqueness.

    Args:
    source (str): The path to the source directory whose contents are to be backed up.
    target (str): The path to the target directory where the backup will be stored.

    The function uses the current date and time to create a unique folder for each backup. If the exact folder name 
    is already taken, it appends a number to create a unique path. Errors during the backup process are caught, 
    and an error message is printed followed by exiting the script.
    """
    try:
        current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_folder = target + '/Problem_' + problem_idx + '_' + current_date
        if os.path.exists(backup_folder):
            it = 2
            while os.path.exists(backup_folder + '_' + str(it)):
                it += 1
            backup_folder = backup_folder + '_' + str(it)
        copytree(source, backup_folder)
    except Exception as e:
        print("Error:", e)
        sys.exit(1)


def make_inputs_outputs(xml_root, problem_folder, polygon_folder):
    """
    Copies input and output files from polygon_folder based on configurations in xml_root to problem_folder.

    Args:
    xml_root (ElementTree): The XML root element containing problem configuration.
    problem_folder (str): The destination folder for organized input and output files.
    polygon_folder (str): The source folder containing unorganized test cases.
    """
    # Extract all testsets directories from XML
    test_dirs = [element.attrib['name'] for element in xml_root.find('judging').findall('testset')]

    try:
        # Iterate over each directory and process files
        for idx, test_dir in enumerate(test_dirs, start=1):
            test_dir_path = str(os.path.join(polygon_folder, test_dir))
            if os.path.isdir(test_dir_path):
                for filename in os.listdir(test_dir_path):
                    if filename.endswith('.a'):  # Identify output files
                        input_filename = filename[:-2]  # Corresponding input file name

                        if not os.path.exists(os.path.join(test_dir_path, input_filename)):
                            raise FileNotFoundError(f"Input file '{input_filename}' not found in {test_dir}.")

                        # Define target paths for input and output files
                        output_file_path = os.path.join(problem_folder, 'output', f"{input_filename}.{idx}")
                        input_file_path = os.path.join(problem_folder, 'input', f"{input_filename}.{idx}")

                        # Copy output and then input files to their respective directories
                        copy(os.path.join(test_dir_path, filename), output_file_path)
                        copy(os.path.join(test_dir_path, input_filename), input_file_path)

    except Exception as e:
        print("Error:", e)
        sys.exit(1)


def get_limits(xml_root):
    """
    Extracts the time and memory limits from an XML root element.

    Args:
    xml_root (ElementTree): The root of the XML configuration for the problem.
    problem_idx (str): Identifier for the problem, used for error messages.

    Returns:
    tuple: Contains computed clang time limit in seconds, repetitions, and memory limit in MB.
    """
    try:
        testset = xml_root.find('judging').find('testset')
        if testset is None:
            raise ValueError("Testset configuration is missing in the provided XML.")

        time_limit_milliseconds = int(testset.find('time-limit').text)
        memory_limit = int(testset.find('memory-limit').text) // (1024 ** 2)  # Convert to MB

        # Using gcd to compute lcm
        gcd_time = gcd(1000, time_limit_milliseconds)
        clang_timelimit = (1000 * time_limit_milliseconds) // gcd_time
        repetitions = clang_timelimit // time_limit_milliseconds
        clang_timelimit //= 1000  # Convert milliseconds to seconds

        if clang_timelimit > 10:
            print(f"[WARNING] Problem with time limit greater than 10 seconds for C/C++!")

        return clang_timelimit, repetitions, memory_limit
    except ValueError as ve:
        print("Error in processing limits:", ve)
        sys.exit(1)
    except Exception as e:
        print("Error:", e)
        sys.exit(1)


def get_problem_name(xml_root):
    """
    Extracts the problem name from an XML document, preferring Portuguese over English.

    Args:
    xml_root (Element): The root element of an XML document containing problem details.

    Returns:
    str: The name of the problem either in English or Portuguese.

    The function searches for the problem name first in English and then in Portuguese.
    If no name is found, it raises a ValueError.
    """
    try:
        problem_name = None
        for name_element in xml_root.findall('.//names/name'):
            if name_element.attrib.get('language') == 'english':
                problem_name = name_element.attrib.get('value')
                break

        for name_element in xml_root.findall('.//names/name'):
            if name_element.attrib.get('language') == 'portuguese':
                problem_name = name_element.attrib.get('value')
                break
        if problem_name is None:
            raise ValueError("Problem name not found in the XML file.")
        problem_name = problem_name.replace(r'\&', '&')
        return problem_name
    except Exception as e:
        print("Error:", e)
        sys.exit(1)


def make_description(polygon_folder, xml_root, problem_folder, problem_idx):
    """
    Creates a problem description file and copies the problem statement PDF.

    Args:
    polygon_folder (str): Source folder containing the problem's assets.
    xml_root (Element): The XML root element containing problem configuration.
    problem_folder (str): Destination folder where the problem's description should be stored.
    problem_idx (str): The problem index or identifier used to name files.
    """
    try:
        # Get problem name from XML
        problem_name = get_problem_name(xml_root)

        # Construct path to the problem statement PDF
        problem_pdf_path = os.path.join(polygon_folder, 'statements', '.pdf', 'portuguese', 'problem.pdf')
        if not os.path.exists(problem_pdf_path):
            raise FileNotFoundError("Portuguese problem statement PDF not found in the provided package.")

        # Ensure description directory exists
        description_folder = os.path.join(problem_folder, 'description')

        # Create and write to the problem.info file
        info_file_path = os.path.join(description_folder, 'problem.info')
        with open(info_file_path, 'w') as problem_info_file:
            print(f'basename="{problem_idx}"', file=problem_info_file)
            print(f'fullname="{problem_name}"', file=problem_info_file)
            print(f'descfile="{problem_idx}.pdf"', file=problem_info_file)

        # Copy the problem statement PDF to the description folder
        copy(problem_pdf_path, description_folder + '/' + problem_idx + '.pdf')

    except FileNotFoundError as e:
        print("File not found error:", e)
        sys.exit(1)
    except IOError as e:
        print("IO error:", e)
        sys.exit(1)
    except Exception as e:
        print("Unexpected error:", e)
        sys.exit(1)


def check_run_directory():
    """
    Ensures that the script is run from its own directory. Exits the program if it is not.
    """
    try:
        # Get the current working directory
        current_directory = os.getcwd()

        # Get the absolute directory of the script
        script_directory = os.path.dirname(os.path.abspath(__file__))

        # Compare both paths and raise an exception if they do not match
        if current_directory != script_directory:
            raise EnvironmentError("The script must be run from the folder it is located in.")

    except EnvironmentError as e:
        print("Error:", e)
        sys.exit(1)


if __name__ == '__main__':
    """
    Main entry point of the script. Parses command line arguments, performs initial setup,
    and orchestrates the execution of the main functionalities of the script.

    The script processes a polygon package based on the provided problem identifier and zip file,
    applying configurations and preparing it for a competitive programming environment.

    Command Line Arguments:
    1. Problem Identifier (str): A single uppercase letter representing the problem.
    2. Polygon Package (str): Path to the zip file containing the problem package.
    3. Java Time Limit Factor (int, optional): Multiplier for the Java time limit relative to C/C++.
    4. Python Time Limit Factor (int, optional): Multiplier for the Python time limit relative to C/C++.

    Exits with status code 1 if an error occurs during argument validation or any subsequent operations.
    """

    check_run_directory()

    problem_idx, file_name, java_tl_factor, python_tl_factor = validate_arguments(sys.argv)

    problem_folder = "/tmp/Problem_" + problem_idx
    polygon_folder = '/tmp/polygon_package'
    clean_directory(problem_folder)
    clean_directory(polygon_folder)

    ensure_dir_exists('packages')
    packages_folder = 'packages/Problem_' + problem_idx

    ensure_dir_exists('backups')
    ensure_dir_exists('zip_packages')

    ensure_dir_exists(problem_folder)
    for folder in os.listdir('problem_template'):
        copytree('problem_template/' + folder, problem_folder + '/' + folder)
    ensure_dir_exists(problem_folder + '/input')
    ensure_dir_exists(problem_folder + '/output')
    ensure_dir_exists(problem_folder + '/description')
    ensure_dir_exists(problem_folder + '/limits')
    ensure_dir_exists(problem_folder + '/compare')
    ensure_dir_exists(problem_folder + '/run')

    ensure_dir_exists(polygon_folder)

    print("\n========================================\n")
    print("Making problem " + problem_idx + " from " + file_name)
    print("[*] Java timelimit factor is " + str(java_tl_factor))
    print("[*] Python timelimit factor is " + str(python_tl_factor) + "\n")

    print("Unzipping package...\n")
    unzip_and_check_polygon_package(file_name, polygon_folder)

    xml_tree = eT.parse(polygon_folder + '/problem.xml')
    xml_root = xml_tree.getroot()

    print("Creating input and output files...\n")
    make_inputs_outputs(xml_root, problem_folder, polygon_folder)

    print("Getting time and memory limits from problem.xml...\n")
    clang_timelimit, repetitions, memory_limit = get_limits(xml_root)
    java_timelimit = clang_timelimit * java_tl_factor
    python_timelimit = clang_timelimit * python_tl_factor

    print("Creating limits files...\n")
    limits_folder = problem_folder + '/limits'
    make_limits(limits_folder, repetitions, memory_limit, clang_timelimit, java_timelimit, python_timelimit)

    print("Creating checker...\n")
    # Copy checker files to compare folder to accept custom checkers
    compare_folder = problem_folder + '/compare'
    if os.path.exists(polygon_folder + '/check.cpp') and os.path.exists(polygon_folder + '/files/testlib.h'):
        copy(polygon_folder + '/check.cpp', compare_folder + '/check.cpp')
        copy(polygon_folder + '/files/testlib.h', compare_folder + '/testlib.h')
        if sys.platform == 'linux':
            if which('g++') is not None:
                print("Compiling checker locally...\n")
                os.system(f"g++ -O2 --std=c++17 {compare_folder}/check.cpp -o {compare_folder}/check")
        elif which('linux_compile') is not None:
            print("Compiling checker remotely...\n")
            os.system(f"linux_compile {compare_folder}/check.cpp")


    print("Creating description files...\n")
    # Copy problem statement PDF to description folder and create problem.info file
    make_description(polygon_folder, xml_root, problem_folder, problem_idx)

    if os.path.exists(packages_folder):
        print("Backing up previous package...\n")
        backup(packages_folder, 'backups', problem_idx)
        if os.path.exists('zip_packages/Problem_' + problem_idx + '.zip'):
            os.remove('zip_packages/Problem_' + problem_idx + '.zip')
        rmtree(packages_folder)

    print("Zipping package...\n")
    make_archive('zip_packages/Problem_' + problem_idx, 'zip', problem_folder)

    print("Moving package to packages folder...\n")
    copytree(problem_folder, packages_folder)

    print("Done!\n")

    print("========================================\n")
