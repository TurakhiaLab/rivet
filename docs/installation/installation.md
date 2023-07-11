# Install RIVET On Your Machine

## Installing RIVET Backend using Docker
!!! Install
    Install `Docker` on your machine first.
    
For ease of use, the entire `RIVET` backend pipeline, including recombinant ranking, is contained within a pre-built public docker image.

### Running RIVET Backend Locally On Your Machine
A `RIVET` backend job can be run locally on your machine.
To launch a Docker shell, run the following two commands.
```
docker run -it mrkylesmith/ripples_pipeline:latest
```
This will run an interactive `Docker` shell with the necessary `RIVET` environment.

<br>

Type the following command to ensure your `RIVET` backend environment is configured correctly, and then proceed to the next steps for running a `RIVET` backend job: [Inferring Recombinants Using the RIVET Backend](installation/upload.md)

```
python3 rivet-backend.py --help
```

<hr>
<br>


### Running RIVET Backend On Google Cloud
We also provide the build-in option of running a parallelized `RIVET` job across a user specified number of Google Cloud Platform (GCP) machines.

!!! setup
    If you would like to use GCP, please see the following docs for setting up an account with Google Cloud Platform: [GCP Setup Docs](../gcp_setup.md)

!!! important
    Put your GCP service account key file (obtained following the docs linked above) in the corresponding location as the command below or update the location in the command below:

To launch a Docker shell using GCP, run the following two commands providing your GCP Authentication keys file.

```
KEY=~/.config/gcloud/<key_file.json>
docker run -it -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/<key_file.json> -v ${KEY}:/tmp/keys/<key_file.json>:ro mrkylesmith/ripples_pipeline:latest
```

<hr>
<br>

## Install RIVET Frontend Locally On Your Machine 

### Clone RIVET Repo Locally
```
git clone https://github.com/TurakhiaLab/rivet.git
cd rivet
```

### Conda Install
!!! Install
    Install `Conda` on your machine first.

All the `RIVET` frontend dependencies have been added to Conda environment setup, that can be found in the `install` directory.

<br>

Run the following commands to activate the `rivet` Conda environment.
```
conda env create -f install/rivet_env.yml
conda activate rivet
```
<br>

Type the following command to ensure your `RIVET` frontend environment is configured correctly, and then proceed to the next steps for using the `RIVET` frontend: [Visualizing Your Results Using the RIVET Frontend](installation/analysis.md)

```
python3 rivet-frontend.py --help
```