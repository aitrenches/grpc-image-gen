import os
import grpc
import image_generation_pb2
import image_generation_pb2_grpc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Server address and API key
SERVER_ADDRESS = os.getenv("SERVER_ADDRESS")
API_KEY = os.getenv("API_SECRET_KEY")

def generate_image(prompt, size="1024x1024"):
    # Create a gRPC channel and stub
    channel = grpc.insecure_channel(SERVER_ADDRESS)
    stub = image_generation_pb2_grpc.ImageGenerationServiceStub(channel)

    # Create a request object
    request = image_generation_pb2.ImageRequest(
        prompt=prompt,
        size=size,
        api_key=API_KEY
    )

    # Call the GenerateImage method
    try:
        response = stub.GenerateImage(request)
        print("Image Generated Successfully!")
        print(f"Base64 Image Data: {response.image[:100]}...")
    except grpc.RpcError as e:
        print(f"Error: {e.code()} - {e.details()}")

if __name__ == "__main__":
    generate_image("A futuristic city skyline at sunset")
