
import os
import libs.config as config
print(f"config.DATABASE_URL: {config.DATABASE_URL}")
print(f"os.getenv('DATABASE_URL'): {os.getenv('DATABASE_URL')}")
print(f"config.__file__: {config.__file__}")
