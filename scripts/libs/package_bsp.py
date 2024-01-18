#!/usr/bin/env python3

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju@amd.com>
#
# SPDX-License-Identifier: MIT

import argparse
import logging
import os
import random
import string
import sys
import tempfile
import bitbake_utils
import package_common
import plnx_utils
import plnx_vars

logger = logging.getLogger('PetaLinux')


ProjectEssentials = 'pre-built project-spec components .petalinux user .gitignore README README.hw'
PackageBspDict = {}


def AddProjectData(proj_key):
    ''' Adding Project path to Dictionary'''
    def f(arg):
        if arg:
            arg = plnx_utils.argreadlink(arg)
        if arg and proj_key:
            rmdstr = ''.join(random.choices(
                string.ascii_uppercase + string.digits, k=5)
            )
            tmp_key = proj_key + '@' + rmdstr
            plnx_utils.add_dictkey(PackageBspDict, tmp_key, 'Path', arg)
        return arg
    return f


def AddHwProjData(hw_key, append=False):
    ''' Adding HW Path to Project in Dictionary'''
    def f(arg):
        if arg:
            arg = plnx_utils.argreadlink(arg)
        if arg and hw_key:
            ProjectKeys = [key for key in PackageBspDict.keys()
                           if key.startswith('Project')]
            if ProjectKeys:
                lastprojkey = ProjectKeys[-1]
                plnx_utils.add_dictkey(PackageBspDict, lastprojkey,
                                       hw_key, arg, append, sep=' ')
            else:
                raise argparse.ArgumentTypeError(
                    '-p/--project option must be specified before --hwsource %s' % (arg))

        return arg
    return f


def AddWorkspaceRecipes(args, project):
    ''' Add Devtool Workspace recipe changes'''
    output = bitbake_utils.run_bitbakecmd(
        'devtool status', project, shell=True, checkcall=False)
    DevtoolStatusDict = {}
    for line in output[0].splitlines():
        if not line.startswith(('NOTE', 'ERROR', 'INFO', 'WARNING')):
            comp, path = line.split(':')
            DevtoolStatusDict[comp] = path
    if DevtoolStatusDict:
        logger.info('Applying workspace changes. This may take time !')
        plnx_utils.setup_plnwrapper(args, project, '', '')
        for recipe in DevtoolStatusDict.keys():
            devtool_cmd = 'devtool finish %s %s -f' % (
                recipe, plnx_vars.MetaUserDir.format(project))
            bitbake_utils.run_bitbakecmd(
                devtool_cmd, project, shell=True, checkcall=False)
            DevtoolAtticDir = os.path.join(
                plnx_utils.get_workspace_path(project), 'attic', 'sources', recipe)
            plnx_utils.RemoveDir(DevtoolAtticDir)


def PackageBsp(args, proot):
    ''' Package the BSP for given projects'''
    if not args.project:
        logger.error('Please specify a PetaLinux project to package the BSP')
        sys.exit(255)
    # Output file not endswith .bsp add it
    PackageName = args.output
    if not PackageName.endswith('.bsp'):
        PackageName = '%s.bsp' % args.output
    package_common.CheckOutFile(PackageName, args.force)

    logger.info('Target BSP "%s" will contain the following projects' %
                PackageName)
    # Get the Exclude file
    ExcludeFile = args.exclude_from_file
    if ExcludeFile and not os.path.isfile(ExcludeFile):
        logger.error('BSP filter file "%s" doesnot exist.' % ExcludeFile)
        sys.exit(255)
    else:
        filehandle = tempfile.NamedTemporaryFile()
        ExcludeFile = filehandle.name
        plnx_utils.add_str_to_file(ExcludeFile, plnx_vars.BspFilesExcludeStr)

    # Create Tmp Directory for project
    Dirhandle = tempfile.TemporaryDirectory()
    TmpBspDir = Dirhandle.name
    plnx_utils.CreateDir(TmpBspDir)
    ProjBaseNames = ''
    # Get Project keys which starts with Project@ from Dict
    ProjectKeys = [key for key in PackageBspDict.keys()
                   if key.startswith('Project@')]
    # Itirate through each key to get Path and Hw project
    for projkey in ProjectKeys:
        for proj in PackageBspDict[projkey].get('Path').split():
            if not os.path.exists(proj):
                logger.error(
                    'Failed to package BSP! Failed to locate project %s!' % proj)
                sys.exit(255)
            logger.info('PetaLinux project: %s' % proj)
            # Add workspace changes
            if not args.exclude_workspace and \
                    os.path.exists(plnx_vars.EsdkInstalledDir.format(proj)):
                AddWorkspaceRecipes(args, proj)
            # Add Project Dirs/Files
            TmpProjDir = os.path.join(TmpBspDir, os.path.basename(proj))
            plnx_utils.CreateDir(TmpProjDir)
            for Dir in ProjectEssentials.split():
                act_file = os.path.join(proj, Dir)
                if os.path.exists(act_file):
                    logger.info('   Copying %s' % act_file)
                    rsync_cmd = 'rsync -a --exclude-from="%s" "%s" "%s/"' % (
                        ExcludeFile, act_file, TmpProjDir)
                    plnx_utils.runCmd(
                        rsync_cmd, out_dir=os.getcwd(), shell=True)
            ProjBaseNames += ' %s' % (os.path.basename(proj))
            plnx_utils.update_config_value('CONFIG_TMP_DIR_LOCATION',
                                           '"${PROOT}/build/tmp"',
                                           plnx_vars.SysConfFile.format(TmpProjDir))
            plnx_utils.remove_str_from_file(
                plnx_vars.MetaDataFile.format(TmpProjDir),
                'HARDWARE_PATH')
            # Add Hwprojects
            for HwDir in PackageBspDict[projkey].get('HWSource', '').split():
                TmpHwProjDir = os.path.join(TmpProjDir, 'hardware')
                plnx_utils.CreateDir(TmpHwProjDir)
                logger.info('   Copying Hardware Project %s' % HwDir)
                rsync_cmd = 'rsync -a --exclude-from="%s" \
                            --exclude={"*.log","*.jou","workspace","implementation"} "%s" "%s/"' % (
                    ExcludeFile, HwDir, TmpHwProjDir)
                plnx_utils.runCmd(
                    rsync_cmd, out_dir=os.getcwd(), shell=True)

    # Create a tar file
    logger.info('Creating BSP')
    logger.info('Generating package %s' % os.path.basename(PackageName))
    plnx_utils.CreateDir(os.path.dirname(PackageName))
    tar_cmd = 'tar -C "%s" -cf - %s | xz -9 -T%s > %s' % (
        TmpBspDir, ProjBaseNames, args.threads, PackageName)
    plnx_utils.runCmd(tar_cmd, out_dir=os.getcwd(), shell=True)


def pkgbsp_args(bsp_parser):
    bsp_parser.add_argument('-o', '--output', default='BSP0',
                            help='BSP package name - <BSP_NAME>.bsp', type=os.path.realpath)
    bsp_parser.add_argument('-p', '--project', metavar='PROJECT_DIR', type=AddProjectData('Project'),
                            help='Specify full path to a PetaLinux project to include in BSP'
                            '(Allow Multiple).', action='append')
    bsp_parser.add_argument('--hwsource', action='append', default=[],
                            type=AddHwProjData('HWSource', append=True),
                            help='Include a hardware source for PetaLinux project'
                            )
    bsp_parser.add_argument('--exclude-from-file', metavar='EXCLUDE_FILE',
                            help='Excludes the files specified in EXCLUDE_FILE'
                            )
    bsp_parser.add_argument('--exclude-workspace', action='store_true',
                            help='Excludes the changes in workspace'
                            )
    bsp_parser.add_argument('-T', '--threads', metavar='NUM', type=int, default=0,
                            help='Use at most NUM threads while packaging the BSP.'
                            '\nDefault is 0 which uses as many threads as there are processor cores.'
                            )
    bsp_parser.set_defaults(func=PackageBsp)

    return
