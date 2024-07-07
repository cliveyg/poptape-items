import uuid

def getPublicID():
    return str(uuid.uuid4())

def exceptionFactory(exception, message):
    return exception(message)