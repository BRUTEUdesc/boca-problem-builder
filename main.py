#!/usr/bin/env python3

import math
import os
import shutil
from distutils.dir_util import copy_tree
import zipfile
import sys
import xml.etree.ElementTree as ET


def make_limits_clang(problem_folder, timelimit, repetitions, memory_limit):
    limit_files = [open(os.path.join(problem_folder, 'limits/c'), 'w'),
                   open(os.path.join(problem_folder, 'limits/cc'), 'w'),
                   open(os.path.join(problem_folder, 'limits/cpp'), 'w'),
                   open(os.path.join(problem_folder, 'limits/rs'), 'w')]
    for limit_file in limit_files:
        print('echo', end=' ', file=limit_file)
        print(timelimit, file=limit_file)
        print('echo', end=' ', file=limit_file)
        print(repetitions, file=limit_file)
        print('echo', end=' ', file=limit_file)
        print(memory_limit, file=limit_file)
        print('echo 1024', file=limit_file)
        print('exit 0', file=limit_file)


def make_limits_java(problem_folder, timelimit, repetitions, memory_limit):
    limit_files = [open(os.path.join(problem_folder, 'limits/java'), 'w'),
                   open(os.path.join(problem_folder, 'limits/kt'), 'w')]
    for limit_file in limit_files:
        print('echo', end=' ', file=limit_file)
        print(timelimit, file=limit_file)
        print('echo', end=' ', file=limit_file)
        print(repetitions, file=limit_file)
        print('echo', end=' ', file=limit_file)
        print(memory_limit, file=limit_file)
        print('echo 1024', file=limit_file)
        print('exit 0', file=limit_file)


def make_limits_python(problem_folder, timelimit, repetitions, memory_limit):
    limit_files = [open(os.path.join(problem_folder, 'limits/py3'), 'w'),
                   open(os.path.join(problem_folder, 'limits/py2'), 'w')]
    for limit_file in limit_files:
        print('echo', end=' ', file=limit_file)
        print(timelimit, file=limit_file)
        print('echo', end=' ', file=limit_file)
        print(repetitions, file=limit_file)
        print('echo', end=' ', file=limit_file)
        print(memory_limit, file=limit_file)
        print('echo 1024', file=limit_file)
        print('exit 0', file=limit_file)


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 main.py {PROBLEM LETTER} POLYGON_PACKAGE.zip [java_tl_factor] [python_tl_factor]")
        exit(1)

    problem_idx = sys.argv[1]
    file_name = sys.argv[2]

    JAVA_TIMELIMIT_FACTOR = 1  # Base is clang timelimit
    PYTHON_TIMELIMIT_FACTOR = 1
    if len(sys.argv) > 3:
        JAVA_TIMELIMIT_FACTOR = int(sys.argv[3])
    if len(sys.argv) > 4:
        PYTHON_TIMELIMIT_FACTOR = int(sys.argv[4])

    if problem_idx not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' or len(problem_idx) != 1:
        print("The problem letter must be a capital letter")
        exit(1)

    if not os.path.exists(file_name):
        print("The file " + file_name + " does not exist")
        exit(1)

    if file_name[-4:] != '.zip':
        print("The file must be a zip file")
        exit(1)

    print("\n========================================\n")
    print("Making problem " + problem_idx + " from " + file_name)
    print("[*] Java timelimit factor is " + str(JAVA_TIMELIMIT_FACTOR))
    print("[*] Python timelimit factor is " + str(PYTHON_TIMELIMIT_FACTOR) + "\n")

    print("Unzipping package...\n")

    target_dir = "/tmp/polygon_package"
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.mkdir(target_dir)
    with zipfile.ZipFile(file_name, 'r') as zip_ref:
        zip_ref.extractall(target_dir)

    if not os.path.exists(target_dir + '/problem.xml'):
        print("The zip file does not seem to be a polygon package")
        exit(1)

    xml_tree = ET.parse(target_dir + '/problem.xml')
    xml_root = xml_tree.getroot()

    if not os.path.exists('packages'):
        os.mkdir('packages')
    if not os.path.exists('backup'):
        os.mkdir('backup')
    if not os.path.exists('zip_packages'):
        os.mkdir('zip_packages')

    # <name language="english" value="Another Trip"/>
    # <name language="portuguese" value="Outra Viagem"/>

    problem_name = None

    for name_element in xml_root.findall('.//names/name'):
        if name_element.attrib.get('language') == 'english':
            problem_name = name_element.attrib.get('value')
            break

    for name_element in xml_root.findall('.//names/name'):
        if name_element.attrib.get('language') == 'portuguese':
            problem_name = name_element.attrib.get('value')
            break

    problem_description = target_dir + '/statements/.pdf/portuguese/problem.pdf'
    os.rename(problem_description, target_dir + '/statements/.pdf/portuguese/' + problem_idx + '.pdf')
    problem_description = target_dir + '/statements/.pdf/portuguese/' + problem_idx + '.pdf'

    os.mkdir(target_dir + '/input')
    os.mkdir(target_dir + '/output')

    dirs = []
    for element in xml_root.find('judging').findall('testset'):
        dirs.append(element.attrib['name'])

    print("Copying input and output files to temporary folder...\n")

    next_id = 1
    for directory in dirs:
        for file in os.listdir(os.path.join(target_dir, directory)):
            if file.endswith('.a'):  # output
                file_input = file[:-2]  # removes .a

                shutil.copy(os.path.join(target_dir, directory, file),
                            os.path.join(target_dir, 'output', str(next_id)))

                shutil.copy(os.path.join(target_dir, directory, file_input),
                            os.path.join(target_dir, 'input', str(next_id)))

                next_id += 1

    problem_input_folder = target_dir + '/input'
    problem_output_folder = target_dir + '/output'

    testset = xml_root.find('judging').find('testset')

    real_timelimit = int(testset.find('time-limit').text)

    clang_timelimit = real_timelimit // 1000  # seconds

    repetitions = 1

    if real_timelimit % 1000 != 0:
        print("[*] Problem " + problem_idx + " with non-integer time limit ({} ms), fixing...".format(real_timelimit))
        clang_timelimit = math.lcm(1000, real_timelimit)
        repetitions = clang_timelimit // real_timelimit
        clang_timelimit //= 1000  # seconds
        print("Now clang timelimit is " + str(clang_timelimit) + "s")
        print("Repetitions is " + str(repetitions))
        total_testing_time = clang_timelimit * repetitions
        print("Total testing time is " + str(total_testing_time) + "s")
        if total_testing_time > 10:
            print("[WARNING] Problem " + problem_idx + " with testing time greater than 10 seconds!\n")
        else:
            print()

    java_timelimit = clang_timelimit * JAVA_TIMELIMIT_FACTOR
    python_timelimit = clang_timelimit * PYTHON_TIMELIMIT_FACTOR

    memory_limit = int(testset.find('memory-limit').text) // (1024 ** 2)  # MB

    problem_folder = 'packages/Problem_' + problem_idx

    if os.path.isdir(problem_folder):
        print("Backuping previous problem " + problem_idx + "...\n")
        backup_number = 1
        backup_folder = 'backup/Problem_' + problem_idx + '-' + str(backup_number)
        while os.path.isdir(backup_folder):
            backup_number += 1
            backup_folder = 'backup/Problem_' + problem_idx + '-' + str(backup_number)
        copy_tree(problem_folder, backup_folder)
        shutil.rmtree(problem_folder)
    os.mkdir(problem_folder)

    print("Creating package...\n")

    copy_tree('problem_template', problem_folder)
    copy_tree(problem_input_folder, os.path.join(problem_folder, 'input'))
    copy_tree(problem_output_folder, os.path.join(problem_folder, 'output'))
    problem_info_file = open(os.path.join(problem_folder, 'description/problem.info'), 'w')
    print('basename=' + problem_idx, file=problem_info_file)
    print('fullname=' + problem_name, file=problem_info_file)
    print('descfile=' + problem_description.split('/')[-1], file=problem_info_file)
    shutil.copy(problem_description, os.path.join(problem_folder, 'description/.'))
    problem_info_file.close()
    make_limits_clang(problem_folder, clang_timelimit, repetitions, memory_limit)
    make_limits_java(problem_folder, java_timelimit, repetitions, memory_limit)
    make_limits_python(problem_folder, python_timelimit, repetitions, memory_limit)

    print("Zipping package...\n")

    shutil.make_archive('zip_packages/Problem_' + problem_idx, 'zip', problem_folder)
    print("========================================\n")
