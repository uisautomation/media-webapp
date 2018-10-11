FROM node:10

# Do everything relative to /usr/src/app which is where we install our
# application.
WORKDIR /usr/src/app

# Install any packages
ADD ./ui/frontend/package*.json ./
RUN npm install

# Copy the remaining files
ADD ./ui/frontend/ ./

# The frontend webapp folders will be mounted here as volumes.
VOLUME /usr/src/app/src
VOLUME /usr/src/app/public

# By default, use the development server to serve the application
ENTRYPOINT ["npm"]
CMD ["start"]
