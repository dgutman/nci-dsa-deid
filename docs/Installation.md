# Installation Instructions

### Clone Repo via SSH or HTML
    git clone git@github.com:dgutman/nci-dsa-deid.git
or
    git clone https://github.com/dgutman/nci-dsa-deid.git

### Other requirements
Docker must be installed, including the docker compose plugin.  This varies depending on the platform.  
The user who will start/stop the DSA container(s) also needs to be able to start the docker containers themselves.  This can usually be done by adding them to the 
the docker user group.

#### Weird Dockerisms
There are two versions of docker compose, on some bundles /installations you can type "docker compose" and the compose is a module within the main docker function.  In other instances, 
you need to type docker-compose.  This is a script version.  I think under the hood one of the versions is written in golang (so faster?), but they seem to have the same basic functionality.
You may need to tweak the start-up script if your system uses docker-compose vs docker compose.  

    
### You can either build the docker containers locally or pull from upstream

I normally create a little start up script to start and stop the docker services.  
The script contents look like this, and it's called start_dsadeid.sh which can be invoked from the devops/nci-dsa-deid directory


    docker compose down
    DSA_USER=$(id -u):$(id -g) DSA_PORT=8080 docker compose up  -d


### Starting the DSA DeID Service
    bast start_dsadeid.sh
