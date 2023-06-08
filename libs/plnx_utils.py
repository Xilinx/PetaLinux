#!/usr/bin/env python

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju@amd.com>
#
# SPDX-License-Identifier: MIT

import os
import subprocess
import re
import sys
import shutil

import logging
logger = logging.getLogger('PetaLinux')

def CreateDir(dirpath):
    '''Creates Directory'''
    if not os.path.exists(dirpath):
        try:
            os.makedirs(dirpath, exist_ok=True)
        except IOError:
            logger.error('Unable to create directory at %s' % dirpath)
            sys.exit(255)

def CreateFile(filepath):
    '''Creates a empty File'''
    if not os.path.isfile(filepath):
        with open(filepath, 'w') as f:
            pass


def RenameDir(indir, outdir):
    '''Rename the Directory'''
    if os.path.exists(indir):
        shutil.move(indir, outdir)


def RenameFile(infile, outfile):
    '''Rename File'''
    if os.path.exists(infile):
        os.rename(infile, outfile)


def RemoveDir(dirpath):
    '''Remove Directory'''
    if os.path.exists(dirpath):
        shutil.rmtree(dirpath)


def RemoveFile(filepath):
    '''Remove file'''
    if os.path.exists(filepath):
        os.remove(filepath)


def CopyDir(indir, outdir):
    '''Copy Directory to Directory'''
    if os.path.exists(indir):
        if not os.path.exists(outdir):
            CreateDir(outdir)
        import distutils.dir_util
        distutils.dir_util.copy_tree(indir, outdir)


def CopyFile(infile, dest, follow_symlinks=False):
    '''Copy File to Dir'''
    if os.path.isfile(infile):
        shutil.copy2(infile, dest, follow_symlinks=follow_symlinks)


def runCmd(command, out_dir, failed_msg='', shell=False):
    '''Run Shell commands from python'''
    command = command.split() if not shell else command
    process = subprocess.Popen(command,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=shell,
                               cwd=out_dir)
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        raise Exception('\n%s\n%s\n%s' %
                        (stdout.decode('utf-8'),
                         stderr.decode('utf-8'),
                         failed_msg))
    else:
        if not stdout is None:
            stdout = stdout.decode("utf-8")
        if not stderr is None:
            stderr = stderr.decode("utf-8")
    return stdout, stderr


def replace_str_fromdir(dirpath, search_str, replace_str, include_dir_names=False):
    '''Replace the string with string in the files and directory names
    Gets the all files from dirpath and search for the given search_str
    replace with replace_str if found in file and filenames
    '''
    for dname, dirs, files in os.walk(dirpath):
        for fname in files:
            fpath = os.path.join(dname, fname)
            try:
                with open(fpath) as f:
                    s = f.read()
                    for string in search_str.split():
                        s = s.replace(string, replace_str)
            except UnicodeDecodeError:
                pass
            if include_dir_names:
                fname = fname.replace(search_str, replace_str)
                RemoveFile(fpath)
                fpath = os.path.join(dname, fname)
            with open(fpath, 'w') as f:
                f.write(s)


def get_plnx_projects_from_bsp(source):
    '''Get the Projects from BSP tar ball'''
    contents_cmd = 'tar --exclude="*/*/*" -tzf "%s"' % (source)
    contents, stderr = runCmd(contents_cmd, os.getcwd(), shell=True)
    projects = []
    for content in contents.split():
        project_name = content.split('/')[0]
        projects.append(project_name) if project_name not in projects else ''

    real_proj = []
    for p in projects:
        if os.path.join(p, '.petalinux') in contents:
            real_proj.append(p)

    return real_proj


def add_str_to_file(filename, string, ignore_if_exists=False, mode='w'):
    '''Add string or line into the given file and ignore if already exists in file'''
    lines = []
    string_found = False
    if os.path.exists(filename):
        with open(filename, 'r') as file_data:
            lines = file_data.readlines()
    for line in lines:
        if re.match(string, line):
            string_found = True
    if not ignore_if_exists or not string_found:
        with open(filename, mode) as file_f:
            file_f.write(string)


def update_config_value(macro, value, filename):
    '''Update the value for macro in a given filename'''
    lines = []
    if os.path.exists(filename):
        with open(filename, 'r') as file_data:
            lines = file_data.readlines()
        file_data.close()

    with open(filename, 'w') as file_data:
        for line in lines:
            if re.search('# %s is not set' % macro, line) or re.search('%s=' % macro, line):
                continue
            file_data.write(line)
        if value == 'disable':
            file_data.write('# %s is not set\n' % macro)
        else:
            file_data.write('%s=%s\n' % (macro, value))
    file_data.close()


def get_config_value(macro, filename, Type='bool', end_macro='=y'):
    '''Get the macro value from given filename'''
    lines = []
    if os.path.exists(filename):
        with open(filename, 'r') as file_data:
            lines = file_data.readlines()
        file_data.close()
    value = ''
    if Type == 'bool':
        for line in lines:
            line = line.strip()
            if line.startswith(macro + '='):
                value = line.replace(macro + '=', '').replace('"', '')
                break
    elif Type == 'choice':
        for line in lines:
            line = line.strip()
            if line.startswith(macro) and line.endswith(end_macro):
                value = line.replace(macro, '').replace(end_macro, '')
                break
    elif Type == 'choicelist':
        for line in lines:
            line = line.strip()
            if line.startswith(macro) and line.endswith(end_macro):
                value += ' ' + line.replace(macro, '').replace(end_macro, '')
    elif Type == 'asterisk':
        for line in lines:
            line = line.strip()
            if line.startswith(macro) and re.search(end_macro, line):
                value = line.split('=')[1].replace('"', '')
                break
    return value


def exit_not_plnx_project(proot):
    '''Check the proot is valide or not by checking .petalinux directory'''
    workingdir = os.getcwd()
    parentdir = ''
    if proot:
        proot = os.path.realpath(proot)
    else:
        while True:
            if os.path.exists(os.path.join(workingdir, '.petalinux')):
                proot = workingdir
                if bool(re.search(r"\s", proot)):
                    logger.error('Your project directory %s includes space.'
                          'PetaLinux project directory should not include space.' % (proot))
                    sys.exit(255)
                return proot
            parentdir = os.path.dirname(workingdir)
            if parentdir == workingdir:
                break
            workingdir = parentdir
        logger.error('You are not inside a PetaLinux project. Please specify a PetaLinux project!')
        sys.exit(255)

    if not os.path.exists(os.path.join(proot, '.petalinux')):
        logger.error('"%s" is not a valid PetaLinux project.'
              'Please create a project with petalinux-create -t project first!' % (proot))
        sys.exit(255)

    if bool(re.search(r"\s", proot)):
        logger.error('Your project directory %s includes space.'
              'PetaLinux project directory should not include space.' % (proot))
        sys.exit(255)
    return proot


def petalinux_version_check(proot):
    '''PetaLinux version check'''
    metadata_file = os.path.join(proot, '.petalinux', 'metadata')
    CreateFile(metadata_file)
    proj_version = get_config_value('PETALINUX_VER', metadata_file)
    petalinux_ver = os.environ.get('PETALINUX_VER', '')
    if not proj_version:
        update_config_value('PETALINUX_VER', petalinux_ver, metadata_file)
    elif petalinux_ver != proj_version:
        logger.warning('Your PetaLinux project was last modified by PetaLinux SDK version: "%s"' % (proj_version))
        logger.warning('however, you are using PetaLinux SDK version: "%s"' % (petalinux_ver))
        if os.environ.get('PLNX_IGNORE_VER_CHK', ''):
            logger.warning('PLNX_IGNORE_VER_CHK is set, skip version checking')
            return True
        userchoice = input('Please input "y/Y" to continue. Otherwise it will exit![n]')
        if userchoice in ['y', 'Y', 'yes', 'Yes', 'YEs', 'YES']:
            update_config_value('PETALINUX_VER', petalinux_ver, metadata_file)
            return True
        else:
            return False
    return True

