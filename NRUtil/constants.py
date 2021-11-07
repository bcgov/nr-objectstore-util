""" Declaring constants used by the archive script. """

import os
import dotenv
import sys

envPath = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(envPath):
    print("loading dot env...")
    dotenv.load_dotenv()

OBJ_STORE_BUCKET = os.environ['OBJ_STORE_BUCKET']
OBJ_STORE_SECRET = os.environ['OBJ_STORE_SECRET']
OBJ_STORE_USER = os.environ['OBJ_STORE_USER']
OBJ_STORE_HOST = os.environ['OBJ_STORE_HOST']

# optional params
optionals = ['TEST_OBJ_NAME']
module = sys.modules[__name__]
for optional in optionals:
    if optional in os.environ:
        setattr(module, optional, os.environ[optional])

