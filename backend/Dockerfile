FROM node
WORKDIR /usr/src/app
COPY package*.json ./
RUN npm install
COPY . .
ENV UPLOADS_PATH=/uploads/
CMD [ "npm", "start" ]
