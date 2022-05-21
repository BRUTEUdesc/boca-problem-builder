import os
import shutil
from distutils.dir_util import copy_tree

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

if not os.path.isdir('packages'):
    os.mkdir('packages')
if not os.path.isdir('backup'):
    os.mkdir('backup')

while True:
    print("Input the problem index")
    problem_idx = input()
    print("Input the problem name")
    problem_name = input()
    print("Do you have a description file? (y/n)")
    has_description = input()
    problem_description = ''
    if (has_description.lower() == 'y'):
        print("Input the problem description file location")
        problem_description = input()
    print("Input the inputs folder location")
    problem_input_folder = input()
    print("Input the outputs folder location")
    problem_output_folder = input()
    print("Input the timelimit in seconds for clang")
    clang_timelimit = int(input())
    print("Input the timelimit in seconds for java")
    java_timelimit = int(input())
    print("Input the timelimit in seconds for python")
    python_timelimit = int(input())
    print("Input the number of repetitions")
    repetitions = int(input())
    print("Input the memory limit in Megabytes")
    memory_limit = int(input())

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

    print("Do you want to build another problem? (y/n)")
    another_problem = input()
    if (another_problem.lower() != 'y'): break
