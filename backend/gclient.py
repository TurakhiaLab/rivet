# GCP Client Library Utility Functions 
#
#
from google.cloud import storage
import os
import subprocess
from termcolor import colored

def create_bucket_folder(project_id, bucket_id, folder_path_from_bucket_root, key_path):
    """
    Initialize empty folders at given location on given GCP bucket
    """
    print("Creating empty folder '{}' in '{}' bucket".format(folder_path_from_bucket_root, bucket_id))
    # Check to make sure folder ends with backslash, add if not
    if not folder_path_from_bucket_root.endswith("/"):
        folder_path_from_bucket_root += "/"
    client = storage.Client.from_service_account_json(key_path)
    bucket = client.get_bucket(bucket_id)
    blob = bucket.blob(folder_path_from_bucket_root)
    result = blob.upload_from_string('')

def init_project(key_file, project_id):
     print("Setting GCP Service Account access credentials")
     os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_file
     subprocess.run(["gcloud", "config", "set", "project", project_id])
     subprocess.run(["gcloud", "auth", "activate-service-account", "--key-file", key_file])


def upload_large_file(project_id, bucket_id, folder_path_from_bucket_root, local_file, key_file):
    """
    Upload larger files using gsutil
    eg)    gsutil cp <file> gs://bucket/destination
    """
    # Grant access to storage bucket
    # Format remote file path
    if not folder_path_from_bucket_root.endswith("/"):
        folder_path_from_bucket_root += "/"
    remote_path = "{}{}".format(folder_path_from_bucket_root, local_file)
    # Execute gsutil copy command
    try:
        subprocess.run(["gsutil", "cp", local_file, "gs://{}/{}".format(bucket_id, folder_path_from_bucket_root)])
        print(colored("SUCCESS: {} file uploaded".format(local_file), 'green', attrs=['reverse']))
    except:
        print(colored("ERROR: {} file upload failed".format(local_file), 'red', attrs=['reverse']))
        exit(1);


def upload_small_file(project_id, bucket_id, folder_path_from_bucket_root, local_file, key_path):
    """
    Only use this function for small file uploads, or decrease default CHUNKSIZE: storage.blob._DEFAULT_CHUNKSIZE
    """
    # Check to make sure folder ends with backslash, add if not
    if not folder_path_from_bucket_root.endswith("/"):
        folder_path_from_bucket_root += "/"
    print("Uploading {} to {} bucket at location: {}{}".format(local_file, bucket_id, folder_path_from_bucket_root, local_file))
    client = storage.Client.from_service_account_json(key_path)
    # Client access to bucket will timeout after 10 mins
    try:
        bucket = client.get_bucket(bucket_id, timeout=600.0)
    except google.cloud.exceptions.NotFound:
        print(colored("ERROR: {} bucket does not exist under project id: {}".format(bucket_id, project_id), 'red', attrs=['reverse']))
        exit(1);
    blob = bucket.blob("{}{}".format(folder_path_from_bucket_root,local_file),chunk_size=CHUNKSIZE)
    result = blob.upload_from_filename(local_file)
