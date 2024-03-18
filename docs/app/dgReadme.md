## Build / run instructions from MacBook

    docker build --platform=linux/amd64 -t deid .

## Then
    docker run -it -p8050:8050 --platform=linux/amd64 -v .:/app deid nano d

