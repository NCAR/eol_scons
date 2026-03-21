#! /usr/bin/env python3
# script to query windows dependencies from an executable and add them as entries to the installbuilder xml

import glob
import os
import subprocess

import argparse

def get_dependencies(exe_path):
    """ Return list of dependencies for executable """
    result = subprocess.run(['ldd', exe_path], capture_output=True, text=True)
    return result.stdout.splitlines()

def parse_dependency_location(line):
    """ Return path to dependency file from line in ldd output """
    # format: libunistring-5.dll => /ucrt64/bin/libunistring-5.dll (0x7ffd71ba0000)
    fields = line.split(" ")
    return fields[2] if len(fields) >= 3 else None

def add_dependencies_to_xml(distribution_files, template_path, output_path):
    contents = ""
    with open(template_path) as f:
        contents = f.read()
    comment = "<!-- add windows dependencies here -->"
    if comment in contents:
        contents = contents.replace(comment, distribution_files)
        with open(output_path, "w") as f:
            f.write(contents)
    else:
        print("No comment placeholder in template file to insert dependencies in.")

def main():
    parser = argparse.ArgumentParser(description="Generate installbuilder XML of windows dependency files")
    # scan both GUI Aspen and Aspen-QC dependencies
    parser.add_argument('--exe1', type=str, required=True, help="path to first executable to scan")
    parser.add_argument('--exe2', type=str, required=False, help="path to second executable to scan")
    parser.add_argument('--template', type=str, required=True, help="path to template dependencies xml file")
    parser.add_argument('--output', type=str, required=True, help="file to save template xml to")
    parser.add_argument('--openssl-dir', type=str, default=None,
                        help="directory to search for OpenSSL DLLs (libssl-*.dll, libcrypto-*.dll)")
    args = parser.parse_args()
    
    exe1_path = os.path.join(os.getcwd(), args.exe1)
    template_path = os.path.join(os.getcwd(), args.template)
    output_path = os.path.join(os.getcwd(), args.output)
    
    deps = get_dependencies(exe1_path)

    if (args.exe2):
        exe2_path = os.path.join(os.getcwd(), args.exe2)
        deps += get_dependencies(exe2_path)

    # Find OpenSSL DLLs by glob — they are loaded dynamically by qopensslbackend.dll
    # and do not appear in ldd output, so we search explicitly by pattern.
    openssl_dlls = []
    if args.openssl_dir:
        for pattern in ['libssl-*.dll', 'libcrypto-*.dll']:
            openssl_dlls += glob.glob(os.path.join(args.openssl_dir, pattern))

    distribution_files = ""
    for d in deps:
        depfile = parse_dependency_location(d)
        if not depfile or depfile.startswith("/c/Windows"):
            # assume dependencies in here are normal windows files
            continue
        # don't add duplicates
        if not depfile in distribution_files:
            # msys paths start at /ucrt64 but windows paths (that installbuilder uses) are really c:/msys64/ucrt64
            distribution_files += f"""<distributionFile>
    <origin>/msys64{depfile}</origin>
</distributionFile>"""
    for dll in openssl_dlls:
        openssl_dir_xml = args.openssl_dir.rstrip('/')
        # Strip windows drive letter if present (C:/msys64/ucrt64/bin -> /msys64/ucrt64/bin)
        if len(openssl_dir_xml) > 1 and openssl_dir_xml[1] == ':':
            openssl_dir_xml = openssl_dir_xml[2:]
        depfile = openssl_dir_xml + '/' + os.path.basename(dll)
        # Prepend /msys64 if path is a MSYS2 ucrt64-relative path (eg /ucrt64/...)
        if not depfile.startswith('/msys64'):
            depfile = '/msys64' + depfile
        if not depfile in distribution_files:
            distribution_files += f"""<distributionFile>
    <origin>{depfile}</origin>
</distributionFile>"""
    add_dependencies_to_xml(distribution_files, template_path, output_path)
    
if __name__=="__main__":
    main()
