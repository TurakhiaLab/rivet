# Setup Google Cloud Platform Account
___

## Setup Cloud Console:
!!! info
	Follow these instructions to open Cloud Console, create a project storage bucket (`bucket_id`) and project ID (`project_id`): [Installation and Setup](https://cloud.google.com/deployment-manager/docs/step-by-step-guide/installation-and-setup)


## Enabling GCP APIs

 Click the following link and under the section titled `Before you begin`, go to step 4 (assuming you already have GCP account and have signed in) and click `Enable API`.  [Cloud Life Sciences](https://cloud.google.com/life-sciences/docs/how-tos/getting-started) <br>

Also make sure the following APIs are enabled as well: <br>

* Compute Engine API <br>
* Cloud Logging API <br>

You can enable them at the following link, under the section `Enabling an API` and clicking: [Go to APIs & Services](https://cloud.google.com/endpoints/docs/openapi/enable-api) which will take you to your Google Cloud console `APIs & Services` page if you are signed in.  If you click `+Enable APIS and SERVICES` you will be able to search for and enable these APIs.

<br>

## Add a service account:
Click the Navagation Menu side bar on the GCP Console and go to `IAM & Admin` -> `Service Accounts`. Click `+Create Service Account`. 

<br>

## Create and Download Keys (JSON)
Once you have created a service account, you need to add keys to this serivce account.
<br>

Click the Navagation Menu side bar on the web console and go to `IAM & Admin` -> `Service Accounts` and click on the active service account you just created from the previous step.

Click the `Keys` tab and `ADD KEY` and `Create new key`.  Select `JSON` key type.  A new `<key>.json` file will automatically be downloaded from your browser.

Move this downloaded `<key>.json` file to the following location (or edit the command below for the location of your choice):

```
~/.config/gcloud/<key>.json
```