import argparse
import os
import shutil
import sys
import glob
# forgive me father, for I have sinned
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))
import dragonfly

"""
Generates a dragonfly data directory that combines multiple annotation sets
by copying reference annotation directories and re-writing tsv files.
Annotation directories must start with "annotations-" and all must
be top level directories in the input directory.
If an output directory is not passed in, the output is saved to a directory
<input path>-adjudicate.
"""

parser = argparse.ArgumentParser()
parser.add_argument(
    "path", help="directory with tsv files to adjudicate with corresponding annotation directories")
parser.add_argument("-o", "--output_directory_name",
                    help="optional name for output directory to store reference annotations and updated tsv files to adjudicate")
parser.add_argument("-r", "--reference_annotations", help="annotation directory used as reference annotation set")
parser.add_argument("-e", "--tsv_file_extension", help="optional file extension for tsv files (default is .conll.txt)")
parser.add_argument("-p", "--annotation_dir_prefix", help="optional prefix for annotation directories (default is annotation-)")

args = parser.parse_args()

if os.path.isdir(args.path):
    input_directory = args.path
else:
    print("Error: {} does not exist".format(args.path))
    quit()

if args.output_directory_name:
    output_directory = args.output_directory_name
else:
    if input_directory.endswith('/') or input_directory.endswith("\\"):
        input_dir_formatted = input_directory[0:len(input_directory) - 1]
        output_directory = input_dir_formatted + "-adjudicate"
    else:
        output_directory = input_directory + "-adjudicate"

if os.path.exists(output_directory):
    print("Error: {} already exists".format(output_directory))
    quit()
else:
    os.makedirs(output_directory)

if args.annotation_dir_prefix:
    annotation_dir_prefix = args.annotation_dir_prefix
else:
    annotation_dir_prefix = "annotations-"

if args.reference_annotations:
    reference_annotation_dir_name = args.reference_annotations
    reference_annotation_dir_path = os.path.join(input_directory, reference_annotation_dir_name)
    if not os.path.exists(reference_annotation_dir_path):
        print("Error: {} doesn't exists".format(reference_annotation_dir_path))
        quit()
else:
    reference_annotation_dir_name = None

if args.tsv_file_extension:
    tsv_file_extension = args.tsv_file_extension
else:
    tsv_file_extension = "conll.txt"

manager = dragonfly.AdjudicationManager(input_directory, output_directory,
                                      tsv_file_extension, annotation_dir_prefix,reference_annotation_dir_name)

output_annotations_directory = os.path.join(output_directory, 'annotations')
manager.copy_reference_annotation_files(output_annotations_directory)

annotations_lookup_by_directory, tsv_files_with_annotations = manager.load_annotation_directories()

tsv_file_paths = glob.glob(input_directory + "/*" + tsv_file_extension)
tsv_files = [os.path.basename(tsv_file_path) for tsv_file_path in tsv_file_paths]
tsv_files_with_annotations = [tsv_file for tsv_file in tsv_files if tsv_file in tsv_files_with_annotations]
tsv_files_without_annotations = [tsv_file for tsv_file in tsv_files if tsv_file not in tsv_files_with_annotations]

manager.rewrite_tsv_files_with_annotations(tsv_files_with_annotations,annotations_lookup_by_directory)
manager.copy_tsv_files_without_annotations(tsv_files_without_annotations)
