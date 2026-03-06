#! /usr/bin/env python3
# script to query windows dependencies from an executable and add them as entries to the installbuilder xml

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
    return line.split(" ")[2]

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
    args = parser.parse_args()
    
    exe1_path = os.path.join(os.getcwd(), args.exe1)
    template_path = os.path.join(os.getcwd(), args.template)
    output_path = os.path.join(os.getcwd(), args.output)
    
    deps = get_dependencies(exe1_path)

    if (args.exe2):
        exe2_path = os.path.join(os.getcwd(), args.exe2)
        deps += get_dependencies(exe2_path)

    distribution_files = ""
    for d in deps:
        depfile = parse_dependency_location(d)
        if depfile.startswith("/c/Windows"):
            # assume dependencies in here are normal windows files
            continue
        # don't add duplicates
        if not depfile in distribution_files:
            # msys paths start at /ucrt64 but windows paths (that installbuilder uses) are really c:/msys64/ucrt64
            distribution_files += f"""<distributionFile>
    <origin>/msys64{depfile}</origin>
</distributionFile>"""
    add_dependencies_to_xml(distribution_files, template_path, output_path)
    
if __name__=="__main__":
    main()
