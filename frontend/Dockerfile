FROM node:18-alpine

WORKDIR /app

COPY package*.json ./

RUN npm install

RUN npm run build

RUN npm prune --omit=dev

COPY . .


CMD ["npm", "run", "preview"]
