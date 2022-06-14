import os
import shutil
from distutils.dir_util import copy_tree
from pathlib import Path
import xml.etree.ElementTree as ET

def make_limits_clang(problem_folder, timelimit, repetitions, memory_limit):
    limit_files = [open(os.path.join(problem_folder,'limits/c'),'w'),open(os.path.join(problem_folder,'limits/cc'),'w'),open(os.path.join(problem_folder,'limits/cpp'),'w')]
    for limit_file in limit_files:
        print('echo', end = ' ', file = limit_file)
        print(timelimit, file = limit_file)
        print('echo', end = ' ', file = limit_file)
        print(repetitions, file = limit_file)
        print('echo', end = ' ', file = limit_file)
        print(memory_limit, file = limit_file)
        print('echo 1024', file = limit_file)
        print('exit 0', file = limit_file)

def make_limits_java(problem_folder, timelimit, repetitions, memory_limit):
    limit_file = open(os.path.join(problem_folder,'limits/java'),'w')
    print('echo', end = ' ', file = limit_file)
    print(timelimit, file = limit_file)
    print('echo', end = ' ', file = limit_file)
    print(repetitions, file = limit_file)
    print('echo', end = ' ', file = limit_file)
    print(memory_limit, file = limit_file)
    print('echo 1024', file = limit_file)
    print('exit 0', file = limit_file)


def make_limits_python(problem_folder, timelimit, repetitions, memory_limit):
    limit_files = [open(os.path.join(problem_folder,'limits/py3'),'w'), open(os.path.join(problem_folder,'limits/py2'),'w')]
    for limit_file in limit_files:
        print('echo', end = ' ', file = limit_file)
        print(timelimit, file = limit_file)
        print('echo', end = ' ', file = limit_file)
        print(repetitions, file = limit_file)
        print('echo', end = ' ', file = limit_file)
        print(memory_limit, file = limit_file)
        print('echo 1024', file = limit_file)
        print('exit 0', file = limit_file)

def empty_dir(path):
    for child in path.glob('*'):
        child.unlink()

def make_problem(folder, index=None):
    xml_tree = ET.parse(folder / "problem.xml")
    xml_root = xml_tree.getroot()

    problem_idx = index if index else folder.stem[0].upper()
    problem_name = xml_root.find("names")[0].attrib['value']

    statement = (folder / 'statements/.pdf/portuguese/problem.pdf').resolve()
    problem_description = str(statement)

    inp_path = Path("/tmp/boca-problem-builder/input/")
    inp_path.mkdir(parents=True, exist_ok=True)
    empty_dir(inp_path)
    problem_input_folder = str(inp_path.resolve())

    has_description = 'y'

    out_path = Path("/tmp/boca-problem-builder/output/")
    out_path.mkdir(parents=True, exist_ok=True)
    empty_dir(out_path)
    problem_output_folder = str(out_path.resolve())

    for test in (path / 'tests').glob('*'):
        file_name = f"{problem_idx}_{test.stem}"
        if test.suffix == '.a':
            shutil.copy(test, out_path / file_name)
        else:
            shutil.copy(test, inp_path / file_name)

    testset = xml_root.find('judging').find('testset')

    clang_timelimit = int(testset.find('time-limit').text) // 1000
    java_timelimit = clang_timelimit + 5
    python_timelimit = java_timelimit + 2

    repetitions = 5

    memory_limit = int(testset.find('memory-limit').text) // 1024**2

    print(f"{problem_idx=}")
    print(f"{problem_name=}")
    print(f"{problem_input_folder=}")
    print(f"{problem_output_folder=}")
    print(f"{clang_timelimit=}")
    print(f"{repetitions=}")
    print(f"{memory_limit=}")

    problem_folder = 'packages/Problem_'+problem_idx
    if os.path.isdir(problem_folder):
        backup_number = 1
        backup_folder = 'backup/Problem_'+problem_idx+'-'+str(backup_number)
        while os.path.isdir(backup_folder):
            backup_number += 1
            backup_folder = 'backup/Problem_'+problem_idx+'-'+str(backup_number)
        copy_tree(problem_folder, backup_folder)
        shutil.rmtree(problem_folder)
    os.mkdir(problem_folder)
    copy_tree('problem_template', problem_folder)
    copy_tree(problem_input_folder, os.path.join(problem_folder, 'input'))
    copy_tree(problem_output_folder, os.path.join(problem_folder, 'output'))
    problem_info_file = open(os.path.join(problem_folder,'description/problem.info'),'w')
    print('basename='+problem_idx, file=problem_info_file)
    print('fullname='+problem_name, file=problem_info_file)
    if has_description.lower() == 'y':
        print('descfile='+problem_description.split('/')[-1], file=problem_info_file)
        shutil.copy(problem_description, os.path.join(problem_folder, 'description/.'))
    problem_info_file.close()
    make_limits_clang(problem_folder,clang_timelimit,repetitions,memory_limit)
    make_limits_java(problem_folder,java_timelimit,repetitions,memory_limit)
    make_limits_python(problem_folder,python_timelimit,repetitions,memory_limit)

    shutil.make_archive('zip_packages/Problem_'+problem_idx, 'zip', problem_folder)

if not os.path.isdir('packages'):
    os.mkdir('packages')
if not os.path.isdir('backup'):
    os.mkdir('backup')
if not os.path.isdir('zip_packages'):
    os.mkdir('zip_packages')

if __name__ == '__main__':
    path = Path(input("Enter problem path\n"))
    index = input("Enter problem index. i. e. letter").upper()
    make_problem(path, index)
