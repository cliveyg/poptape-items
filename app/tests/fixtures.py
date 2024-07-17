import uuid

def getPublicID():
    return str(uuid.uuid4())

def getSpecificPublicID():
    return "e3cf14c3-df06-4360-af93-b445c3d78d9e"

def exceptionFactory(exception, message):
    return exception(message)