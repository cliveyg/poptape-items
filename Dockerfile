FROM python:3.12-slim

# this needs to match the directory/package name of the python app
COPY . /items
WORKDIR /items

# remove unwanted files and folders
RUN rm -rf vitems && \
    rm -rf app/tests && \
    mkdir -p /items/log

# Install any needed packages specified in requirements.txt
RUN pip install --upgrade pip
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Make port 8003 available to the world outside this container
EXPOSE 8003

# Define environment variables here
# args are passed it from cli or docker-compose.yml

# Run app.py when the container launches
#CMD ["python", "test.py"]
#ENTRYPOINT ["redis-cli"]
CMD ["gunicorn", "-b", "0.0.0.0:8003", "items:app"]
#CMD ["python", "-u", "run.py"]
