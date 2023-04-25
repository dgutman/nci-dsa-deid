# Installation Instructions

### Clone Repo via SSH or HTML
    git clone git@github.com:dgutman/nci-dsa-deid.git
or
    git clone https://github.com/dgutman/nci-dsa-deid.git

### Other requirements
Docker must be installed, including the docker compose plugin.  This varies depending on the platform.  
The user who will start/stop the DSA container(s) also needs to be able to start the docker containers themselves.  This can usually be done by adding them to the 
the docker user group.
    
### You can either build the docker containers locally or pull from upstream

I normally create a little start up script to start and stop the docker services.  
The script contents look like this, and it's called start_dsadeid.sh which can be invoked from the devops/nci-dsa-deid directory


    docker compose down
    DSA_USER=$(id -u):$(id -g) DSA_PORT=8080 docker compose up  -d


### Starting the DSA DeID Service
    bast start_dsadeid.sh
