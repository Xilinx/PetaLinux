import sys
import os
import re
import subprocess

def get_fragmentcfg_path(config_arg):
  fragment_path = ''
  cmd="bitbake " + config_arg + " -c diffconfig"
  print("[INFO] %s" % (cmd))
  p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  out,err = p.communicate()
  if  err:
    print("ERROR: %s" % (err))
    sys.exit(2)
  print(out.decode("utf-8"))
  for line in out.decode("utf-8").splitlines() :
    if re.search("fragment.cfg",line):
      fragment_path = line.replace(' ','')
  return fragment_path

def generate_bbappend(config_arg,bblayer_path,fragment_path):
    print("generate_bbappend %s %s" % (fragment_path,bblayer_path))
    cmd="recipetool appendsrcfile -wW "+ bblayer_path + " " + config_arg + " " + fragment_path
    print("[INFO] %s" % (cmd))
    p = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    for line in p.stdout:
        if not re.search("WARNING:", line.decode("utf-8")):
            print(line.decode("utf-8").rstrip())
    return

def get_value_from_key(file, key):
    f = open(file, "r")
    for line in f:
        if key in line:
            if '=' in line:
                value = line.split('=')[1]
                value = value.strip('\n').replace('\"','')
                f.close()
                return value
            else:
                f.close()
                return

def append_files(srcfile,dstfile):
# srcfile content will added to dstfile
    try:
        dst = open(dstfile, 'a+')
        src = open(srcfile, 'r')
        dst.write(src.read())
        dst.close()
        src.close()
    except:
        pass

def get_file_size(file_path):
    if os.path.isfile(file_path):
        file_info = os.stat(file_path)
        return file_info.st_size

def highest_powerof2(file_path):
    file_size=get_file_size(file_path)
    if isinstance(file_size, float):
        size_=int(file_size) + 1
    else:
        size_=file_size

    if not size_ & (size_ - 1) == 0 and size_ > 0:
        import math
        p = int(math.log(size_, 2)) + 1
        return int(pow(2, p))
    else:
        return size_

cfg_string = """\
#@TYPE: Machine
#@NAME: @@machine_name@@
#@DESCRIPTION: Petalinux auto generated @@machine_name@@ stub

# Compatibility with old BOARD value
MACHINEOVERRIDES =. "@@machine_overrides@@:"

#### Preamble
MACHINEOVERRIDES =. "${@['', '@@machine_name@@:']['@@machine_name@@' != '${MACHINE}']}"
#### Regular settings follow

@@required_machine_conf@@

@@extra_yocto_vars@@

#### No additional settings should be after the Postamble
#### Postamble
PACKAGE_EXTRA_ARCHS:append = "${@['', ' @@package_arch@@']['@@machine_name@@' != '${MACHINE}']}"
"""

def gen_machinefile(json_file, machine_name, conf_dir):
    import json
    cfg_str = ''
    machine_dir = '%s/machine' %(conf_dir)
    machine_file = '%s/%s.conf' %(machine_dir, machine_name)
    # Dont regenerate if machine file exists
    if os.path.exists(machine_file):
        return
    with open(json_file, 'r') as data_file:
        data = json.load(data_file)
        data_file.close()
    if machine_name and machine_name in data.keys():
        cfg_str = cfg_string.replace('@@machine_name@@',machine_name)
        cfg_str = cfg_str.replace('@@package_arch@@', machine_name.replace('-','_'))
        if 'machine-overrides' in data[machine_name].keys():
            cfg_str = cfg_str.replace('@@machine_overrides@@', data[machine_name]['machine-overrides'])
        if 'required-machine-conf' in data[machine_name].keys():
            if data[machine_name]['required-machine-conf']:
                required_str = 'require conf/machine/%s.conf' % (data[machine_name]['required-machine-conf'])
                cfg_str = cfg_str.replace('@@required_machine_conf@@', required_str)
        yocto_vars_str = ''
        if 'extra-yocto-vars' in data[machine_name].keys():
            yocto_vars_str = '\n'.join(var for var in data[machine_name]['extra-yocto-vars'])
        cfg_str = cfg_str.replace('@@extra_yocto_vars@@', yocto_vars_str)
    if cfg_str:
        mkdir(machine_dir)
        with open(machine_file, 'w') as machine_file_f:
            machine_file_f.write(cfg_str)
        machine_file_f.close()

def mkdir(folderpath,silent_discard = True):
    is_successful = False
    try:
        if os.path.exists(folderpath): is_successful = True
        else:
            if not silent_discard: print("INFO: Creating %s directory" %folderpath)
            os.makedirs(folderpath)
            is_successful = True
    except:
        pass

    if not is_successful:
        print ("Unable to create %s directory " %folderpath)
        sys.exit(1)

def find_mmc_and_gem_status(dtb_file_path):
    dts_file = dtb_file_path.replace('.dtb', '.dts')
    # Run the dtc command to convert DTB to DTS
    subprocess.run(['dtc', '-I', 'dtb', '-O', 'dts', '-o',
        dts_file, dtb_file_path], check=True,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    with open(dts_file, 'r') as file:
        content = file.read()
        sdhci_regexp = ['sdhci[0-9]+']
        gem_regexp = ['gem[0-9]+', 'ethernet.*[0-9]+']
        mmc_counter = []
        gem_counter = []
        symbol_match = re.search(r'__symbols__\s*{([^}]*)}', content)
        symbol_node = symbol_match.group(1) if symbol_match else None
        if symbol_node:
            sdhci_labels = []
            gem_labels = []
            for lablekey in sdhci_regexp:
                sdhci_matches = re.findall(lablekey + r'\s*=\s*([^;]+);', symbol_node)
                sdhci_labels += [match.strip() for match in sdhci_matches]
            for lablekey in gem_regexp:
                gem_matches = re.findall(lablekey + r'\s*=\s*([^;]+);', symbol_node)
                gem_labels += [match.strip() for match in gem_matches]
            mmc_counter = find_node(sdhci_labels, content)
            gem_counter = find_node(gem_labels, content)
    return str(mmc_counter) + '|' + str(gem_counter)

def find_node(labels, content):
    generic_address = None
    generic_status = None
    counter = []
    gem_num = 0
    emmc_mode = 6

    for label in labels:
            generic_match = label.replace('"','').split('/')[2]
            if generic_match:
                generic_node_match = re.search(r'{}(\s*{{\s*[^}}]+}})'.format(re.escape(generic_match)), content)
                gem_num += 1
                if generic_node_match:
                    generic_node_content = generic_node_match.group(1)
                    non_removable_match = re.search(r'non-removable(\s*;)?', generic_node_content)
                    generic_status_match = re.search(r'status\s*=\s*"([^"]+)"', generic_node_content)
                    if generic_status_match:
                        generic_status = generic_status_match.group(1)

            if (generic_node_match and non_removable_match) and (generic_status == "okay" or not generic_status_match):
                return emmc_mode
            elif generic_node_match and (generic_status == "okay" or not generic_status_match):
                counter.append(gem_num-1)

    return counter
