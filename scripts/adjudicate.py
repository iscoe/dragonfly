import argparse
import os
import shutil

"""
Generates a dragonfly data directory that combines multiple annotation sets
by copying reference annotation directories and re-writing tsv files.
Annotation directories must start with "annotations-" and all must
be top level directories in the input directory.
If an output directory is not passed in, the output is saved to a directory
<input path>-disambiguation.
"""


def copy_annotation_files(src_dir, dest_dir):
    src_files = [src_file for src_file in os.listdir(src_dir) if src_file.endswith(".anno")]
    for src_file in src_files:
        src_file_path = os.path.join(src_dir, src_file)
        shutil.copy(src_file_path, dest_dir)


def get_tag_list_formatted(annotation_file_contents_as_list):
    tag_list_formatted = []
    for row in annotation_file_contents_as_list:
        if row == ["\n"]:
            tag_list_formatted.append(" ")
        else:
            # row[0] is the token; row[1] is the tag
            tag_list_formatted.append(row[1].rstrip())
    return tag_list_formatted


def get_tsv_filename_from_anno_filename(annotation_filename):
    return annotation_filename.replace(".anno", "")

def get_anno_filename_from_tsv_filename(tsv_filename):
    return tsv_filename + ".anno"

# get dictionary of existing tags for annotations-2 through annotations-n
def load_annotation_directories(input_dir, reference_annotation_directory_name):
    tsv_files_with_annotations = []

    # TODO: Update pulling of contents - walks are not always returned in a guaranteed order
    input_dir_contents = [x for x in os.walk(input_dir)]
    annotations_lookup_by_sub_directory = {}
    annotation_directories = [sub_dir for sub_dir in input_dir_contents[0][1] if
                              sub_dir.startswith('annotations-') and sub_dir != reference_annotation_directory_name]
    for annotation_directory in annotation_directories:
        annotations_lookup_by_sub_directory[annotation_directory] = {}
        annotation_file_names = [file_name for file_name in os.listdir(os.path.join(input_dir, annotation_directory)) if
                                 file_name.endswith(".anno")]
        for annotation_file_name in annotation_file_names:
            tsv_file_name = get_tsv_filename_from_anno_filename(annotation_file_name)
            if tsv_file_name not in tsv_files_with_annotations:
                tsv_files_with_annotations.append(tsv_file_name)

            f = open(os.path.join(input_dir, annotation_directory, annotation_file_name), "r")
            annotation_file_contents = [row.split('\t') for row in f]
            annotation_file_contents_formatted = get_tag_list_formatted(annotation_file_contents)
            annotations_lookup_by_sub_directory[annotation_directory][annotation_file_name] = annotation_file_contents_formatted

    return annotations_lookup_by_sub_directory, tsv_files_with_annotations


def has_header(connl_file):
    if connl_file[0].isupper() and connl_file[0].startswith("TOKEN"):
        return True
    else:
        return False


def rewrite_tsv_file_with_tags(file_write, source_tsv_file, reference_annotations_for_tsv_file):
    annotation_col_names = list(reference_annotations_for_tsv_file.keys())

    # check if connl has header
    if has_header(source_tsv_file):
        header_index = 0
        header_offset = -1
        row_tokens = source_tsv_file[header_index].rstrip().split('\t')
        line = [row_tokens[0]] + annotation_col_names + row_tokens[1:len(row_tokens)]
        file_write.write("\t".join(line) + "\n")
    else:
        header_index = -1
        header_offset = 0
        row_tokens = source_tsv_file[header_index + 1].rstrip().split('\t')
        line = ["TOKEN"] + annotation_col_names + ['COLUMN_' + str(x) for x in range(1, len(row_tokens))]
        file_write.write("\t".join(line) + "\n")

    for i in range(header_index + 1, len(source_tsv_file)):
        row_tokens = source_tsv_file[i].rstrip().split('\t')
        if len(row_tokens[0]) == 0:
            file_write.write('\n')
        else:
            # first column is the TOKEN
            file_write.write(row_tokens[0])
            file_write.write('\t')

            # next columns are the annotation tags from the annotation directories
            for k in range(0, len(annotation_col_names)):
                annotation_col_name = annotation_col_names[k]
                file_write.write(reference_annotations_for_tsv_file[annotation_col_name][i + header_offset])
                if k != len(annotation_col_names) - 1:
                    file_write.write('\t')

            # last columns are any additional columns the original tsv contained (e.g., translation)
            if len(row_tokens) > 1:
                file_write.write('\t')
                for j in range(1, len(row_tokens)):
                    file_write.write(row_tokens[j])
                    if j != len(row_tokens) - 1:
                        file_write.write('\t')

            file_write.write('\n')


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path", help="directory with tsv files to disambiguate with corresponding annotation directories")
    parser.add_argument("-o", "--output_directory_name",
                        help="optional name for output directory to store reference annotations and updated tsv files to disambiguate")
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
            output_directory = input_dir_formatted + "-disambiguation"
        else:
            output_directory = input_directory + "-disambiguation"

    if os.path.exists(output_directory):
        print("Error: {} already exists".format(output_directory))
        quit()
    else:
        os.makedirs(output_directory)

    if args.annotation_dir_prefix:
        annotation_dir_prefix = args.annotation_dir_prefix
    else:
        annotation_dir_prefix = "annotation-"

    if args.reference_annotations:
        reference_annotation_dir_name = args.reference_annotations
        reference_annotation_dir_path = os.path.join(input_directory, reference_annotation_dir_name)
        if not os.path.exists(reference_annotation_dir_path):
            print("Error: {} doesn't exists".format(reference_annotation_dir_path))
            quit()

        output_annotations_directory = os.path.join(output_directory, 'annotations')
        os.makedirs(output_annotations_directory)

        copy_annotation_files(reference_annotation_dir_path, output_annotations_directory)
    else:
        reference_annotation_dir_name = None

    if args.tsv_file_extension:
        tsv_file_extension = args.tsv_file_extension
    else:
        tsv_file_extension = "conll.txt"

    # get dictionary of existing tags for annotations-2 through annotations-n
    '''
    Example:
    {
        "annotations-1": {
                    "tsv_file_1": [["B-PER"],["I-PER"],...["O"]]
                    "tsv_file_2": [["O"],["B-LOC"],...["B-GPE"]]
                    "tsv_file_4": [["O"],["O"],...["O"]]

                }
        "annotations-2": {
                    "tsv_file_1": [["B-PER"],["O"],...["O"]]
                    "tsv_file_2": [["O"],["B-LOC"],...["O"]]
                    "tsv_file_3": [["B-GPE"],["I-GPE"],...["O"]]
                }

    }
    '''
    annotations_lookup_by_directory, tsv_files_with_annotations = load_annotation_directories(input_directory,
                                                                                              reference_annotation_dir_name)

    input_dir_contents = [x for x in os.walk(input_directory)]

    # TODO: Update pulling of contents - walks are not always returned in a guaranteed order
    tsv_files = [filename for filename in input_dir_contents[0][2] if filename.endswith(tsv_file_extension)]
    tsv_files_with_annotations = [tsv_file for tsv_file in tsv_files if tsv_file in tsv_files_with_annotations]
    tsv_files_without_annotations = [tsv_file for tsv_file in tsv_files if tsv_file not in tsv_files_with_annotations]

    # if the tsv file has annotations re-write the tsv file with the annotations as a new column
    for tsv_file in tsv_files_with_annotations:
        annotation_file_name = get_anno_filename_from_tsv_filename(tsv_file)

        f_read = open(os.path.join(input_directory, tsv_file), "r")
        f_write = open(os.path.join(output_directory, tsv_file), "w")

        src_tsv_file = f_read.read().split("\n")

        additional_annotations_for_tsv = {}
        for annotation_directory in annotations_lookup_by_directory.keys():
            if annotation_file_name in annotations_lookup_by_directory[annotation_directory].keys():
                additional_annotations_for_tsv[annotation_directory] = \
                annotations_lookup_by_directory[annotation_directory][annotation_file_name]

        rewrite_tsv_file_with_tags(f_write, src_tsv_file, additional_annotations_for_tsv)

    # if the file does not have any annotations copy it over
    # TODO: if updated tsvs now have headers - these should as welll
    for tsv_file in tsv_files_without_annotations:
        shutil.copyfile(os.path.join(input_directory, tsv_file), os.path.join(output_directory, tsv_file))
