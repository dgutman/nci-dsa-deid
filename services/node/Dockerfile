# FROM node:15.6.0
FROM --platform=linux/amd64 node:18.16.0

ARG NODE_ENV=development

ENV NODE_ENV=${NODE_ENV}

RUN mkdir -p /home/node/app

WORKDIR /home/node/app/

COPY package.json .

RUN npm install

COPY . .

