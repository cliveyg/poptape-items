FROM python:3.12-alpine

# add bash etc as alpine version doesn't have these
RUN apk add --no-cache bash git gawk sed grep bc coreutils 

# this modules enable use to build bcrypt
RUN apk --no-cache add --virtual build-dependencies gcc g++ make libffi-dev
#RUN pip install bcrypt==2.0.0
RUN apk add --no-cache redis

# this needs to match the directory/package name of the python app
COPY . /items
WORKDIR /items

# remove unwanted files and folders
RUN rm -rf vitems
RUN rm -rf app/tests
RUN mkdir -p /items/log
#RUN touch /items/log/poptape_items.log


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
