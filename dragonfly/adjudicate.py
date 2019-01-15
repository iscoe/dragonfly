import glob
import os
import random
import shutil


class AdjudicationManager(object):
    def __init__(self, input_dir, output_dir, tsv_file_ext, anno_dir_prefix, ref_annos=None):
        self.input_directory = input_dir
        self.output_directory = output_dir
        self.tsv_file_extension = tsv_file_ext
        self.annotation_dir_prefix = anno_dir_prefix

        if ref_annos is None:
            # check if annotations/ exists
            if os.path.exists(os.path.join(self.input_directory, "annotations")):
                self.reference_annotations = "annotations"
            else:
                self.reference_annotations = self.get_random_reference_annotation_dir()
        else:
            self.reference_annotations = ref_annos

    def get_annotation_directories(self):
        annotation_dirs_paths = glob.glob(self.input_directory + "/" + self.annotation_dir_prefix + "*")
        annotation_dirs = [os.path.basename(annotation_dir_path) for annotation_dir_path in annotation_dirs_paths if
                           os.path.basename(annotation_dir_path) != self.reference_annotations]
        return annotation_dirs

    def get_random_reference_annotation_dir(self):
        annotation_dirs = self.get_annotation_directories()
        return random.choice(annotation_dirs)

    def get_identifier_from_annotation_dir(self, annotation_dir):
        return annotation_dir.replace(self.annotation_dir_prefix, "")

    def load_annotation_directories(self):
        tsv_files_with_annotations = []

        annotations_lookup_by_sub_directory = {}
        annotation_directories = self.get_annotation_directories()

        for annotation_directory in annotation_directories:
            annotations_lookup_by_sub_directory[annotation_directory] = {}

            annotation_file_paths = glob.glob(os.path.join(self.input_directory, annotation_directory) + "/*.anno")

            for annotation_file_path in annotation_file_paths:
                annotation_file_name = os.path.basename(annotation_file_path)
                tsv_file_name = self.get_tsv_filename_from_anno_filename(annotation_file_name)
                if tsv_file_name not in tsv_files_with_annotations:
                    tsv_files_with_annotations.append(tsv_file_name)

                f = open(annotation_file_path, "r")
                annotation_file_contents = [row.split('\t') for row in f]
                annotation_file_contents_formatted = self.get_tag_list_formatted(annotation_file_contents)
                annotations_lookup_by_sub_directory[annotation_directory][
                    annotation_file_name] = annotation_file_contents_formatted

        return annotations_lookup_by_sub_directory, tsv_files_with_annotations

    def rewrite_tsv_file_with_tags(self, file_write, source_tsv_file, reference_annotations_for_tsv_file):
        annotation_col_names = list(reference_annotations_for_tsv_file.keys())
        annotation_col_ids = [self.get_identifier_from_annotation_dir(annotation_col_name) for
                              annotation_col_name in annotation_col_names]
        # check if tsv has header
        if self._has_header(source_tsv_file):
            header_index = 0
            header_offset = -1
            row_tokens = source_tsv_file[header_index].rstrip().split('\t')
            line = [row_tokens[0]] + annotation_col_ids + row_tokens[1:len(row_tokens)]
            file_write.write("\t".join(line) + "\n")
        else:
            header_index = -1
            header_offset = 0
            row_tokens = source_tsv_file[header_index + 1].rstrip().split('\t')
            line = ["TOKEN"] + annotation_col_ids + ['COLUMN_' + str(x) for x in range(1, len(row_tokens))]
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

    def copy_reference_annotation_files(self, dest_dir):
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        src_dir = os.path.join(self.input_directory, self.reference_annotations)
        src_files = [src_file for src_file in glob.glob(src_dir + "/*.anno")]
        for src_file in src_files:
            src_file_path = os.path.join(src_file)
            shutil.copy(src_file_path, dest_dir)

    @staticmethod
    def get_tag_list_formatted(annotation_file_contents_as_list):
        tag_list_formatted = []
        for row in annotation_file_contents_as_list:
            if row == ["\n"]:
                tag_list_formatted.append(" ")
            else:
                # row[0] is the token; row[1] is the tag
                tag_list_formatted.append(row[1].rstrip())
        return tag_list_formatted

    @staticmethod
    def get_tsv_filename_from_anno_filename(annotation_filename):
        return annotation_filename.replace(".anno", "")

    @staticmethod
    def get_anno_filename_from_tsv_filename(tsv_filename):
        return tsv_filename + ".anno"

    @staticmethod
    def _has_header(tsv_file):
        if tsv_file[0].isupper() and tsv_file[0].startswith("TOKEN"):
            return True
        else:
            return False
