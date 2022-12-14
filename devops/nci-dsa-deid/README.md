## I am blending the docker compose files from the current DSA master branch
## And adding in some customizations I have extracted from the dsa-wsi-deid branch

### Notes
So I am creating a local dockerfile that preinstalls torch for the wsi-deid plugin


docker build -t dsa_nci_deid .
Otherwise the docker-compose script will fail since it doesn't have access to the
correct image, this is done for speed as well so I don't have to keep rerunning this


## Provision.py
To minimize the number of changes I am making to the main dsa provision.py script, I have
made a copy of the provision.py script form the dsa-wsi-deid, and am importing this
into the provision.py script ( import wsideid_provision ) and then just calling the two functions
that the wsideid provisioning script references
