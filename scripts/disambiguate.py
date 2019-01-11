import argparse
import os
import shutil
import itertools
import pprint


def copy_annotation_files(src_dir, dest_dir):
    src_files = os.listdir(src_dir)
    for file_name in src_files:
        full_file_name = os.path.join(src_dir, file_name)
        if (os.path.isfile(full_file_name)):
            shutil.copy(full_file_name, dest_dir)


def format_token_list(list_to_split):
    new_list = []
    for token in list_to_split:
        if token == ["\n"]:
            new_list.append(" ")
        else:
            new_list.append(token[1].rstrip())
    return new_list


def load_additional_annotation_directories(input_dir, reference_annotation_dir_name):
    # get dictionary of existing tags for annotations-2 through annotations-n
    input_dir_contents = [x for x in os.walk(input_dir)]
    annotations_lookup_by_sub_directory = {}
    additional_annotations = []
    for sub_directory in input_dir_contents[0][1]:
        if sub_directory.startswith('annotations-') and sub_directory != reference_annotation_dir_name:
            additional_annotations.append(sub_directory)
            annotations_lookup_by_sub_directory[sub_directory] = {}
            for file_name in os.listdir(os.path.join(input_dir, sub_directory)):
                if file_name.endswith(".anno"):
                    annotation_file_contents = []

                    f = open(os.path.join(
                        input_dir, sub_directory, file_name), "r")
                    for x in f:
                        token_tag_list = x.split('\t')
                        annotation_file_contents.append(token_tag_list)
                    annotations_lookup_by_sub_directory[sub_directory][file_name] = annotation_file_contents
    return annotations_lookup_by_sub_directory


def rewrite_conll_file_with_tags(f_write, og_connl_file, reference_annoations_for_connl):
    #HEADER_INDEX = 0
    #read_tokens = og_connl_file[HEADER_INDEX].rstrip().split('\t')
    #line = [read_tokens[HEADER_INDEX]] + list(reference_annoations_for_connl.keys()) + read_tokens[HEADER_INDEX+1:len(read_tokens)]
    #f_write.write("\t".join(line) +"\n")

    for i in range(0, len(og_connl_file)):
        read_tokens = og_connl_file[i].rstrip().split('\t')
        # print(read_tokens)
        if len(read_tokens[0]) == 0:
            # print('hit')
            f_write.write('\n')
        else:
            f_write.write(read_tokens[0])
            f_write.write('\t')

            keys = list(reference_annoations_for_connl.keys())
            for k in range(0, len(keys)):
                key = keys[k]
                f_write.write(reference_annoations_for_connl[key][i])
                if k != len(keys) - 1:
                    f_write.write('\t')

            if len(read_tokens) > 1:
                for j in range(1, len(read_tokens)):
                    f_write.write(read_tokens[j])
                    if j != len(read_tokens)-1:
                        f_write.write('\t')

            f_write.write('\n')


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "path", help="directory with tsv files to disambiguate with corresponding annotation directories")
    parser.add_argument("-n", "--directory_name",
                        help="optional name for output directory to store reference annotations and updated tsv files to disambiguate")
    parser.add_argument("-r", "--reference_annotations",
                        help="annotation directory used as reference annotation set")

    args = parser.parse_args()

    if os.path.isdir(args.path):
        input_dir = args.path
    else:
        print("Error: {} does not exist".format(args.path))
        quit()

    # copy output directory
    if input_dir.endswith('/') or input_dir.endswith("\\"):
        base_path_formmated = input_dir[0:len(input_dir)-1]
    disambiguation_path = base_path_formmated + "-disambiguation"

    if os.path.exists(disambiguation_path):
        print("Error: {} already exists".format(disambiguation_path))
        quit()
    else:
        os.makedirs(disambiguation_path)
        dest_dir = os.path.join(disambiguation_path, 'annotations')
        os.makedirs(dest_dir)

        # copy reference annotations to disambiguation directory
        src_dir = input_dir + "/annotations-1"
        dest_dir = os.path.join(disambiguation_path, 'annotations')
        copy_annotation_files(src_dir, dest_dir)

        # get dictionary of existing tags for annotations-2 through annotations-n
        annotations_lookup_by_sub_directory = load_additional_annotation_directories(
            input_dir, "annotations-1")
        anno_files = [annofile_tags.keys()
                      for annofile_tags in annotations_lookup_by_sub_directory.values()]
        original_tsv_filename = [item.replace(
            ".anno", "") for sublist in anno_files for item in sublist]
        original_tsv_filename_unique = list(set(original_tsv_filename))
        input_dir_contents = [x for x in os.walk(input_dir)]
        conll_files = [filename for filename in input_dir_contents[0]
                       [2] if filename.endswith('conll.txt')]

        for conll_file in conll_files:
            # if the connl file has annotations
            if conll_file in original_tsv_filename_unique:
                f_read = open(os.path.join(args.path, conll_file), "r")
                f_write = open(os.path.join(
                    disambiguation_path, conll_file), "w")

                og_connl_file = f_read.read().split("\n")

                reference_annoations_for_connl = {}
                for reference_annotation in annotations_lookup_by_sub_directory.keys():
                    # check if the connl has annoations for this anoo dir
                    if conll_file + ".anno" in annotations_lookup_by_sub_directory[reference_annotation].keys():
                        formatted_tags = format_token_list(
                            annotations_lookup_by_sub_directory[reference_annotation][conll_file + ".anno"])
                        reference_annoations_for_connl[reference_annotation] = formatted_tags
                rewrite_conll_file_with_tags(
                    f_write, og_connl_file, reference_annoations_for_connl)

            # if the file does not have annoations just copy it over
            else:
                shutil.copyfile(os.path.join(input_dir, conll_file), os.path.join(
                    disambiguation_path, conll_file))
