# Installation Instructions

### Clone Repo via SSH or HTML
    git clone git@github.com:dgutman/nci-dsa-deid.git
or
    git clone https://github.com/dgutman/nci-dsa-deid.git

## Install dependencies
On many systems these may be installed, for Ubuntu systems


    sudo apt-get install unzip git 


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

## Monitoring the DSA status

Since the DSA is run via docker, you can use docker commands to make sure everything is running and not throwing errors.  One thing that happens on some systems, is that the latest version of MONGO uses certain instruction
sets that are not available on all computers.  I've seen this issue primarily on virtualized servers, in which case you may see the mongo service constantly restarting.


## Breaking the DSA
![image](https://user-images.githubusercontent.com/713166/234358613-ef910a5f-6963-4d32-b35e-f7d0236fcbe1.png)
So in the above example, I actually started the DSA twice (oops!).  So the thing to notice is the nci-dsa-deid-_mongodb_1 container keeps saying restarting.

I can see what's going on by using the docker logs function, in this case
    docker logs -f nci-dsa-deid_mongodb_1

![image](https://user-images.githubusercontent.com/713166/234358849-ab4948be-c340-488b-9679-d120d65cca0d.png)

## Debugging the error
In this example, it's having issues writtng the mongodb log file.  This is because the db directory that docker is trying to write data into has the wrong permissions.  ls -al
