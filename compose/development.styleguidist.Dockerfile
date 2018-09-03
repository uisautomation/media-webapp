FROM node:10

# Do everything relative to /usr/src/app which is where we install our
# application.
WORKDIR /usr/src/app

# Install any packages
ADD ./frontend/package*.json ./
RUN npm install

# By default, use the development server to serve the application
ENTRYPOINT ["npm"]
CMD ["start"]
