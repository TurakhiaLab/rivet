"""
Script to upload the necessary files to GCP Storage Bucket before running RIPPLES pipeline job.
Files:
    gisaidAndPublic.$date.masked.pb
    gisaidAndPublic.$date.metadata.tsv.gz
    gisaid_fullNames_$date.fa.xz
    metadata_batch_$date.tsv.gz
    cog_all.fasta.xz
    genbank.fa.xz
"""
from backend import gclient
from backend import util
import argparse


def format_files(date):
    metadata = "gisaidAndPublic.{}.metadata.tsv.gz".format(date)
    mat = "gisaidAndPublic.{}.masked.pb".format(date)
    gisaid_seqs = "gisaid_fullNames_{}.fa.xz".format(date)
    gisaid_meta = "metadata_batch_{}.tsv.gz".format(date)
    # Note, make sure the following two files coorespond to the given date.
    # Make sure the correct files have been retrieved
    ncbi_seqs = "cog_all.fasta.xz"
    cog_uk_seqs = "genbank.fa.xz"
    files = [metadata, mat, gisaid_seqs, gisaid_meta, ncbi_seqs, cog_uk_seqs]
    for file in files:
        # Check that each file exists in current directory
        util.check_file_exists(file)
    return files

def arg_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-d", "--date", required=True, type=str, help="Given input data of the MAT treealigner to use")
    parser.add_argument("-b", "--bucket_id", required=True, type=str, help="Name of GCP bucket to upload files to.")
    parser.add_argument("-f", "--bucket_folder", required=True, type=str, help="Name of folder on GCP bucket where all data for RIPPLES job will be written.")
    parser.add_argument("-p", "--project_id", required=True, type=str, help="GCP Project ID (account) that will be used to run RIPPLES job")
    parser.add_argument("-k", "--key_path", required=True, type=str, help="Full path to Serivce Account Keys file on local filesystem, in order to grant GCP access")
    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = arg_parser()
    
    # Format correct files to upload
    files = format_files(args.date)

    # Setup credentials
    gclient.init_project(args.key_path, args.project_id)

    if not args.bucket_folder.endswith("/"):
        folder_path_from_bucket_root = args.bucket_folder + "/data"
    else:
        folder_path_from_bucket_root = args.bucket_folder + "data"

    # Create data directory inside given bucket_folder for RIPPLES job
    gclient.create_bucket_folder(args.project_id, args.bucket_id, folder_path_from_bucket_root, args.key_path)

    print("Uploading files to '{}' location on '{}' bucket".format(folder_path_from_bucket_root, args.bucket_id))

    for file in files:
        gclient.upload_large_file(args.project_id, args.bucket_id, folder_path_from_bucket_root, file, args.key_path)
    print(colored("DONE: All files needed for RIPPLES job uploaded.", 'green', attrs=['reverse']))
