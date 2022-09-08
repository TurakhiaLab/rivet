## Setup your Google Cloud Platform Account
___

1. **Setup Cloud Console:**
	- If needed, please follow these instructions to open Cloud Console, create a project storage bucket (`bucket_id`) and project ID (`project_id`): [Installation and Setup](https://cloud.google.com/deployment-manager/docs/step-by-step-guide/installation-and-setup)

<br>

2. **Enabling APIs**

	- Click the following link and under the section titled `Before you begin`, go to step 4 (assuming you already have GCP account and have signed in) and click `Enable API`.  [Cloud Life Sciences](https://cloud.google.com/life-sciences/docs/how-tos/getting-started) <br>

	- Also make sure the following APIs are enabled as well:
		- **Compute Engine API**
		- **Cloud Logging API**
	- You can enable them at the following link, under the section `Enabling an API` and clicking: [Go to APIs & Services](https://cloud.google.com/endpoints/docs/openapi/enable-api) which will take you to your Google Cloud console `APIs & Services` page if you are signed in.  If you click `+Enable APIS and SERVICES` you will be able to search for and enable these APIs.

<br>

3. **Add a service account**:
	- Click the Navagation Menu side bar on the GCP Console and go to `IAM & Admin` -> `Service Accounts`. Click `+Create Service Account`. 

<br>

4. **Create and Download Keys (JSON)**
	- Once you have created a service account, you need to add keys to this serivce account.
	Click the Navagation Menu side bar on the web console and go to `IAM & Admin` -> `Service Accounts` and click on the active service account you just created from the previous step.

	- Click the `Keys` tab and `ADD KEY` and `Create new key`.  Select `JSON` key type.  A new `<key>.json` file will automatically be downloaded from your browser.

	- Move this downloaded `<key>.json` file to the following location (or edit the command below for the location of your choice):

		```
		~/.config/gcloud/<key>.json
		```

	-  Then run the following command in your terminal to set the environment variable path to the location where you just placed your downloaded `<keys>.json` file. 

	<br>

	**IMPORTANT NOTE:  I would recommend you keep the generated name of the `<keys.json>` file you downloaded, and make sure the naming of all the `<keys.json>` match in the two commands below, and in your `ripples.yaml` configuration file under the `key_file` field, that you will setup once you enter the Docker shell.**


**Then you will run the following two commands to enter the Docker shell:**
```
KEY=~/.config/gcloud/<keys.json>
docker run -it -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/<keys.json> -v ${KEY}:/tmp/keys/<keys.json>:ro mrkylesmith/ripples_pipeline_dev:latest
```
