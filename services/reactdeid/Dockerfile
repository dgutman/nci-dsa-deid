FROM --platform=linux/amd64 node:18.16.0

ARG NODE_ENV=development

ENV NODE_ENV=${NODE_ENV}

RUN mkdir -p /home/reactdeid/app

WORKDIR /home/reactdeid/app/

COPY ./package.json .

RUN npm install

RUN mkdir node_modules/.cache && chmod -R 777 node_modules/.cache

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]

