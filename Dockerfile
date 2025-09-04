FROM node:20-alpine

WORKDIR /workspace

RUN apk add --no-cache \
    git \
    bash \
    openssh-client \
    python3 \
    make \
    g++ \
    postgresql-client

COPY package*.json ./

RUN npm ci

COPY . .

RUN npx prisma generate

EXPOSE 3000

CMD ["npm", "run", "dev"]