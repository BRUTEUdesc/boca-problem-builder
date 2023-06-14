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
    if len(sys.argv) != 3:
        print("Usage: python3 main.py {PROBLEM LETTER} POLYGON_PACKAGE.zip")
        exit(1)

    problem_idx = sys.argv[1]
    file_name = sys.argv[2]

    if problem_idx not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' or len(problem_idx) != 1:
        print("The problem letter must be a capital letter")
        exit(1)

    if file_name[-4:] != '.zip':
        print("The file must be a zip file")
        exit(1)

    target_dir = "/tmp/polygon_package"
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.mkdir(target_dir)
    with zipfile.ZipFile(file_name, 'r') as zip_ref:
        zip_ref.extractall(target_dir)

    xml_tree = ET.parse(target_dir + '/problem.xml')
    xml_root = xml_tree.getroot()

    os.mkdir(target_dir + '/inputs')
    os.mkdir(target_dir + '/outputs')

    if not os.path.exists('packages'):
        os.mkdir('packages')
    if not os.path.exists('backup'):
        os.mkdir('backup')
    if not os.path.exists('zip_packages'):
        os.mkdir('zip_packages')

    problem_name = xml_root.find("names")[0].attrib['value']

    problem_description = target_dir + '/statements/.pdf/portuguese/problem.pdf'
    os.rename(problem_description, target_dir + '/statements/.pdf/portuguese/' + problem_idx + '.pdf')
    problem_description = target_dir + '/statements/.pdf/portuguese/' + problem_idx + '.pdf'

    if not os.path.exists(target_dir + '/inputs'):
        os.mkdir(target_dir + '/inputs')
    if not os.path.exists(target_dir + '/outputs'):
        os.mkdir(target_dir + '/outputs')

    for directory in os.listdir(target_dir):
        if os.path.isdir(os.path.join(target_dir, directory)) and directory.startswith('test'):
            for file in os.listdir(os.path.join(target_dir, directory)):
                if file.endswith('.a'):
                    shutil.copy(os.path.join(target_dir, directory, file), os.path.join(target_dir, 'outputs'))
                else:
                    shutil.copy(os.path.join(target_dir, directory, file), os.path.join(target_dir, 'inputs'))

    for file in os.listdir(target_dir + '/outputs'):
        file_name = file.split('.')[0]
        os.rename(os.path.join(target_dir + '/outputs', file), os.path.join(target_dir + '/outputs', file_name))

    problem_input_folder = target_dir + '/inputs'
    problem_output_folder = target_dir + '/outputs'

    testset = xml_root.find('judging').find('testset')

    clang_timelimit = int(testset.find('time-limit').text)  # 1000
    java_timelimit = clang_timelimit + 5000
    python_timelimit = clang_timelimit + 2000

    repetitions = 1  # SO MEXE SE PRECISAR

    memory_limit = int(testset.find('memory-limit').text) // (1024 ** 2)

    problem_folder = 'packages/Problem_' + problem_idx

    if os.path.isdir(problem_folder):
        backup_number = 1
        backup_folder = 'backup/Problem_' + problem_idx + '-' + str(backup_number)
        while os.path.isdir(backup_folder):
            backup_number += 1
            backup_folder = 'backup/Problem_' + problem_idx + '-' + str(backup_number)
        copy_tree(problem_folder, backup_folder)
        shutil.rmtree(problem_folder)
    os.mkdir(problem_folder)

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

    shutil.make_archive('zip_packages/Problem_' + problem_idx, 'zip', problem_folder)

