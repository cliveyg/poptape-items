# poptape-items
![All unit tests pass](https://github.com/cliveyg/poptape-items/actions/workflows/unit-test.yml/badge.svg) ![Successfully deployed](https://github.com/cliveyg/poptape-items/actions/workflows/post-merge-deployment.yml/badge.svg) ![Tests passed](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/cliveyg/1c36226cfbdf2ae7928d01649ab54fc3/raw/7186f8aec18604f40e932bd737c6f9ba287fd6f0/poptape-items-junit-tests.json&label=Tests) ![Test coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/cliveyg/1c36226cfbdf2ae7928d01649ab54fc3/raw/7186f8aec18604f40e932bd737c6f9ba287fd6f0/poptape-items-cobertura-coverage.json&label=Test%20coverage) ![release](https://img.shields.io/github/v/release/cliveyg/poptape-items)

Microservice to perform CRUD operations on auction items.

Please see [this gist](https://gist.github.com/cliveyg/cf77c295e18156ba74cda46949231d69) to see how this microservice works as part of the auction system software.

### API routes

To be completed
```
/items/status [GET] (Unauthenticated)
```
Returns a status code of 200 if api is running

### Notes:
None

### Tests:
Tests can be run from app root (/path/to/authy) using: `pytest --cov-config=app/tests/.coveragerc --cov=app app/tests`
Current test coverage is around 96%

### Docker:
This app can now be run in Docker using the included docker-compose.yml and Dockerfile. The database and roles still need to be created manually after successful deployment of the app in Docker. It's on the TODO list to automate these parts :-)

### TODO:
* Complete this documentation!
* Get test coverage to 95%