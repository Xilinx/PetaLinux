#!/usr/bin/env python3

# Copyright (C) 2021-2022, Xilinx, Inc.  All rights reserved.
# Copyright (C) 2022-2023, Advanced Micro Devices, Inc.  All rights reserved.
#
# Author:
#       Raju Kumar Pothuraju <rajukumar.pothuraju@amd.com>
#
# SPDX-License-Identifier: MIT

import logging
import os
import subprocess
import sys
import bitbake_utils
import plnx_utils
import plnx_vars

logger = logging.getLogger('PetaLinux')


def is_tmpdir_nfs(Tmpdir):
    '''Check if the FileSystem is located on NFS and exit if True'''
    if Tmpdir:
        plnx_utils.CreateDir(Tmpdir)
        if plnx_utils.get_filesystem_id(Tmpdir) == '6969':
            logger.error('% s directory is on NFS. Please set local storage for'
                         ' TMPDIR through petalinux-create using --tmpdir.' % Tmpdir)
            sys.exit(255)


def create_tmpdir_ifnfs(cpath, name, tmpdir):
    '''Create the TMPDIR if current filesystem is located in NFS.
    Default TMPDIR location will be /tmp and update system config file'''
    if plnx_utils.get_filesystem_id(cpath) == '6969' and not tmpdir:
        logger.warning(
            'Project on NFS mount, trying to relocate TMPDIR to local storage (/tmp)')
        import random
        import string
        import time
        current_time = time.strftime('%Y.%m.%d-%H.%M.%S', time.localtime())
        def_tmp = '/tmp'
        tmp_dir_name = '%s-%s-%s' % (name, current_time,
                                     ''.join(random.choices(string.ascii_letters, k=3)))
        random_tmpdir = os.path.join(def_tmp, tmp_dir_name)
        plnx_utils.CreateDir(random_tmpdir)
        logger.info('Project TMPDIR is redirecting to %s' % (random_tmpdir))
        plnx_utils.update_config_value(plnx_vars.TmpDirConf, '"%s"' %
                                       random_tmpdir, plnx_vars.SysConfFile.format(cpath))
    elif tmpdir:
        logger.info('Project TMPDIR is redirecting to %s' % (tmpdir))
        plnx_utils.update_config_value(plnx_vars.TmpDirConf, '"%s"' %
                                       tmpdir, plnx_vars.SysConfFile.format(cpath))


def remove_if_component_exists(command, cpath, name):
    '''Take the backup of old directory or file.
    Remove if andy backup copies present already'''
    if command != 'project' or name:
        cpath_backup = cpath.rstrip('/') + '_old'
        # Delete any earlier backup copy
        plnx_utils.RemoveDir(cpath_backup)
        # Rename the current dir
        plnx_utils.RenameDir(cpath, cpath_backup)
        # Rename bb file
        if command != 'project':
            plnx_utils.RenameFile(
                os.path.join(cpath_backup, name + '.bb'),
                os.path.join(cpath_backup, name + '.bb.old')
            )
        plnx_utils.CreateDir(cpath)


def if_component_exists(command, Force, cpath, name):
    '''Give error if cpath already exists in project and force not specified
    Give warning if cpath already exists in project and override
    '''
    if command == 'project' and not name:
        return

    if os.path.exists(cpath):
        if Force:
            logger.warning(
                '"%s" already exists and --force parameter specified, overwriting' % cpath)
        else:
            logger.error(
                'Component "%s" already exists. Use --force option to overwrite' % cpath)
            sys.exit(255)


def SetupAppsModules(args, template_path, cpath, proot):
    '''Copy and Update the apps modules recipe files with the user given data
    template_path - Tool path of where templates were stored
    cpath - Project path of where to copy templates
    proot - Project Directory
    Update recipe file with user specified SRC_URI and STATIC_PN
    '''
    plnx_utils.CopyDir(template_path, cpath)
    recipe_name = args.name
    config_string = 'CONFIG_%s\n' % (args.name)
    plnx_utils.add_str_to_file(
        plnx_vars.UsrRfsConfig.format(proot),
        config_string, ignore_if_exists=True, mode='a+')
    if args.command == 'apps':
        map_str = '@appname@'
    else:
        map_str = '@modname@ @mod_name@'
    for _str in map_str.split():
        plnx_utils.replace_str_fromdir(
            cpath, _str, recipe_name, include_dir_names=True)

    srcuri2add = []
    if args.network_srcuris:
        srcuri2add.extend(args.network_srcuris)
    for srcuri in args.local_srcuris:
        files_dir = os.path.join(cpath, 'files')
        plnx_utils.CopyFile(os.path.realpath(srcuri), files_dir)
        srcuri2add.append('file://%s' % (os.path.basename(srcuri)))

    recipe_path = os.path.join(cpath, '%s.bb' % (args.name))
    if srcuri2add:
        bitbake_utils.bb_updatevar(
            recipe_path, 'SRC_URI', ' '.join(srcuri2add))

    if args.command == 'apps' and args.static_pn:
        bitbake_utils.bb_updatevar(recipe_path, 'STATIC_PN', args.static_pn)


def Createproject(args, proot, cpath):
    ''' Creates the Project using BSP or default TEMPLATE
    It supports having single or multiple Projects in BSP
    Multi project- Default extract the projects in PWD
                   If --name specified ask user which BSP need to be extracted.
    Single project- Extract the project into PWD or specified --name
    Template project- Copy the default project setup from Tool
    '''
    if args.tmpdir:
        is_tmpdir_nfs(args.tmpdir)
    projects2extract = []
    if args.source:
        # BSP project setup
        projects = plnx_utils.get_plnx_projects_from_bsp(args.source)
        if not projects:
            if args.name:
                plnx_utils.RemoveDir(cpath)
            logger.error(
                'No PetaLinux projects found in the BSP %s' % args.source)
            sys.exit(255)
        if args.name:
            defaultproj = projects[0]
            while defaultproj != ' '.join(projects):
                # If component name specified and source has multiple projects
                # Ask users to input the project name or use default project.
                logger.info('Available projects: %s' % (' '.join(projects)))
                user_in = input(
                    'Please type the reference project? (%s):' % defaultproj)
                user_in = user_in.strip()
                refproject = ''
                if not user_in:
                    refproject = defaultproj
                for p in projects:
                    if p == user_in:
                        refproject = p
                if refproject:
                    projects2extract.append(refproject)
                    break
            if not projects2extract:
                projects2extract.append(defaultproj)
        else:
            for p in projects:
                if os.path.exists(p):
                    user_force = False
                    if not args.force:
                        user_in = input(
                            'Project %s/%s already exists. Please input "y" to overwrite:' % (cpath, p))
                        user_in = user_in.strip()
                        if user_in in ['y', 'Y']:
                            user_force = True
                        else:
                            logger.info('Will skip project %s' % p)

                    if args.force or user_force:
                        # Delete any earlier backup copy
                        plnx_utils.RemoveDir(os.path.join(cpath, p) + '_old')
                        # Rename the current dir
                        plnx_utils.RenameDir(os.path.join(cpath, p),
                                             os.path.join(cpath, p) + '_old')
                        projects2extract.append(p)
                else:
                    projects2extract.append(p)

        installed_proj = []
        for project in projects2extract:
            proot = cpath
            if not args.name:
                proot = os.path.join(cpath, project)
            plnx_utils.CreateDir(cpath)
            tar_extraargs = ''
            if len(projects2extract) > 1:
                tar_extraargs = '-C "%s"' % (cpath)
            elif args.name:
                tar_extraargs = '--strip-components=1'
            tar_cmd = 'tar -xJf "%s" "%s" %s' % (
                args.source, project, tar_extraargs)
            msgonfail = 'Failed to extract %s from BSP %s!' % (
                project, args.source)
            cmd_status = plnx_utils.runCmd(
                tar_cmd, cpath, failed_msg=msgonfail, shell=True)
            create_tmpdir_ifnfs(proot, project, args.tmpdir)
            installed_proj.append(project)

        if installed_proj:
            logger.info('Project(s):')
            for p in installed_proj:
                print('\t* %s' % (p))
            logger.info('Has been successfully installed to %s' % (cpath))
    else:
        # template project setup
        if not args.name:
            logger.error(
                'Neither target project name nor PetaLinux project source BSP is specified!')
            sys.exit(255)
        plnx_utils.CreateDir(cpath)
        plnx_utils.CopyDir(
            plnx_vars.TemplateCommon.format(args.command), cpath)
        plnx_utils.CopyDir(plnx_vars.TemplateDir_C.format(
            args.command, args.template),
            cpath)
        # Update the host name and the produdct name of the project
        project_name = os.path.basename(cpath)
        plnx_utils.replace_str_fromdir(cpath, '@projname@', project_name)
        plnx_utils.CreateDir(plnx_vars.MetaDataDir.format(cpath))
        if not os.path.exists(plnx_vars.GitIgnoreFile.format(cpath)):
            plnx_utils.add_str_to_file(
                plnx_vars.GitIgnoreFile.format(cpath),
                plnx_vars.GitIgnoreStr)
        create_tmpdir_ifnfs(cpath, args.name, args.tmpdir)


def Createapps(args, proot, cpath):
    ''' Create Apps for Project'''
    if not os.path.exists(
        plnx_vars.TemplateDir_C.format(args.command, args.template)
    ):
        logger.error('Invalid template %s for %s' % (
            args.command, args.template))
        sys.exit(255)
    SetupAppsModules(args,
                     plnx_vars.TemplateDir_C.format(
                         args.command, args.template),
                     cpath, proot)


def Createmodules(args, proot, cpath):
    ''' Create Modules for Project'''
    SetupAppsModules(args,
                     plnx_vars.TemplateDir_C.format(args.command, 'c'),
                     cpath, proot)


def CreateComponent(args, proot):
    ''' Setup and call the specific funtion for the command'''
    cpath = ''
    if args.command == 'project':
        cpath = os.path.join(args.out, args.name)
    else:
        recipes_path = 'recipes-%s' % (args.command)
        if args.command == 'apps' and \
                args.template in plnx_vars.DFX_Templates.keys():
            recipes_path = 'recipes-firmware'
            logger.warning(
                'Creating "%s" template apps required FPGA Manager \
to be enabled in petalinux-config' % (args.template))
        cpath = os.path.join(plnx_vars.MetaUserDir.format(proot),
                             recipes_path, args.name)

    if_component_exists(args.command, args.force, cpath, args.name)
    remove_if_component_exists(args.command, cpath, args.name)

    if args.command == 'project':
        Createproject(args, proot, cpath)
    elif args.command == 'apps':
        Createapps(args, proot, cpath)
    elif args.command == 'modules':
        Createmodules(args, proot, cpath)
    logger.info('New %s successfully created in %s' % (args.command, cpath))

    # Enable the component
    if args.command in ['apps', 'modules'] and args.enable:
        logger.info('Enabling created component')
        plnx_utils.add_str_to_file(
            plnx_vars.RfsConfig.format(proot),
            'CONFIG_%s=y\n' % args.name, ignore_if_exists=True, mode='a+')
        logger.info('%s has been enabled' % args.name)
