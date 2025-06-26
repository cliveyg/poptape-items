FROM python:3.12-slim

# this needs to match the directory/package name of the python app
COPY . /items
WORKDIR /items
COPY --chmod=755 run_app.sh /items

# remove unwanted files and folders
RUN rm -rf vitems && \
    rm -rf app/tests && \
    mkdir -p /items/log

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 8003 available to the world outside this container
EXPOSE $PORT

# Define environment variables here
# args are passed it from cli or docker-compose.yml

# Run shell script to start gunicorn
CMD ["./run_app.sh"]
