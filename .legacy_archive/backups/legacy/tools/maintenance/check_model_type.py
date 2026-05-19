from deerflow.models import create_chat_model
import os

os.environ["DEER_FLOW_CONFIG_PATH"] = "vendor/deer-flow/config.yaml"

model = create_chat_model(name="groq")
print(f"Model: {model}")
print(f"Type: {type(model)}")
