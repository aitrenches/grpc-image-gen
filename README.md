**Title:**
Migrating an Image Generation API from REST to gRPC for Better Performance

**Introduction**
As the image generation API, powered by OpenAI’s DALL·E, started gaining traction, I realized that a REST-based architecture might not be the most efficient approach for handling multiple concurrent requests. While REST APIs are widely adopted, they come with overheads such as HTTP latency, JSON serialization, and stateless communication. To improve performance, reduce latency, and enable better streaming capabilities, I decided to migrate the REST API service to gRPC.

This article walks through the process of converting an existing Python-based REST API service to a gRPC service, and using OpenAI’s DALLE model for image generation.

---

## **Why RPC Over REST?**
Like many RPC systems, gRPC (Google's Remote Procedure Call) offers several advantages over traditional REST APIs:
- **Binary Serialization**: Uses Protocol Buffers instead of JSON, making communication more efficient.
- **Reduced Latency**: Faster than REST due to HTTP/2 support.
- **Strongly Typed Contracts**: Uses `.proto` files for defining API contracts.
- **Built-in Streaming**: Supports bi-directional streaming, unlike REST.

Given these benefits, gRPC was a natural choice for optimizing the API.

---

## **Notes: **
1. The image generation API already exists in `app.py` and is powered by Flask, a Python web framework.

2. You can clone the repository, create a virtual environment, install dependencies, store environment variables in a `.env` file and follow along

## **Step 1: Defining the Protobuf Schema `image_generation.proto` file**
The first step in converting the REST API to gRPC is defining the `.proto` file, which serves as the contract for communication between the client and the server. Here’s the schema I created from the REST API parameters (i.e prompt, image size, and api key):

```proto
syntax = "proto3";

package imagegeneration;

// Define the request message
message ImageRequest {
    string prompt = 1;
    string size = 2;
    string api_key = 3;
}

// Define the response message
message ImageResponse {
    string image = 1;
}

// Define the gRPC service
service ImageGenerationService {
    rpc GenerateImage (ImageRequest) returns (ImageResponse);
}
```

This schema defines the **ImageGenerationService** with a `GenerateImage` method that takes an `ImageRequest` (containing the prompt, image size, and API key) and returns an `ImageResponse` with the generated image in base64 format.

For more information on how to define the request and response messages of a proto file i.e `Service Definition` please see the [protobuf documentation](https://protobuf.dev/) 

---

## **Step 2: Generating gRPC Stubs**
With the `.proto` file ready, you can generate the necessary gRPC stubs to implement the server and client. To do this, I ran:

```sh
pip install grpcio grpcio-tools
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. image_generation.proto
```

This command generated two files:
- `image_generation_pb2.py` – Contains message classes.
- `image_generation_pb2_grpc.py` – Contains service definitions.

---

## **Step 3: Implementing the gRPC Server**
Next, create the `grpc_server.py` and implement the gRPC service, i.e rewrite `app.py` into gRPC enabled `grpc_server.py`:

```python
import os
import grpc
import openai
from concurrent import futures
import image_generation_pb2
import image_generation_pb2_grpc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in environment variables")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

class ImageGenerationService(image_generation_pb2_grpc.ImageGenerationServiceServicer):
    def GenerateImage(self, request, context):
        if request.api_key != os.getenv("API_SECRET_KEY"):
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("Invalid API key")
            return image_generation_pb2.ImageResponse(image="")

        if not request.prompt:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Prompt is required")
            return image_generation_pb2.ImageResponse(image="")

        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=request.prompt,
                n=1,
                size=request.size or "1024x1024",
                response_format="b64_json"
            )
            return image_generation_pb2.ImageResponse(image=response.data[0].b64_json)
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return image_generation_pb2.ImageResponse(image="")

# Start the gRPC Server
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    image_generation_pb2_grpc.add_ImageGenerationServiceServicer_to_server(ImageGenerationService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("gRPC Server started on port 50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
```

This code initializes a gRPC server, listens on port 50051, and handles image generation requests using OpenAI’s API.

---

## **Step 4: Implementing the gRPC Client**
To test the gRPC server, this is a simple client script in `grpc_client.py`:

```python
import grpc
import image_generation_pb2
import image_generation_pb2_grpc

SERVER_ADDRESS = "localhost:50051"
API_KEY = "test-key"

def generate_image(prompt, size="1024x1024"):
    channel = grpc.insecure_channel(SERVER_ADDRESS)
    stub = image_generation_pb2_grpc.ImageGenerationServiceStub(channel)
    request = image_generation_pb2.ImageRequest(prompt=prompt, size=size, api_key=API_KEY)

    try:
        response = stub.GenerateImage(request)
        print("Image Generated Successfully!")
        print(f"Base64 Image Data: {response.image[:100]}...")
    except grpc.RpcError as e:
        print(f"Error: {e.code()} - {e.details()}")

if __name__ == "__main__":
    generate_image("A futuristic city skyline at sunset")
```

---

## **Final Thoughts**
The `grpc_client.py` can directly call the Image Generation method on the `grpc_server.py` application on a different machine as if it were a local object, making it efficient and easier to create a distributed application and service.

The benefits include:

- ✅ Faster request processing due to HTTP/2
- ✅ Reduced data overhead with Protocol Buffers
- ✅ Strongly typed contracts for better API structure

If you’re building a distributed, high-performance API, consider making the switch to gRPC!

Let me know if you’ve done a similar migration—I’d love to hear your thoughts! 🚀

