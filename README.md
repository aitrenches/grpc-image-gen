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

---

## **How to Run and Test**

### **Prerequisites**
1. **Create a virtual environment** (if you haven't already):
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

3. **Set up environment variables**: Create a `.env` file in the project root with the following:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   API_SECRET_KEY=your_secret_key_for_authentication
   SERVER_ADDRESS=localhost:50051
   ```

### **Running the Flask Server (REST API)**

To run the original Flask REST API server:

```sh
python app.py
```

The Flask server will start on `http://localhost:5000` (default Flask port).

**Testing the Flask server** (using curl or any HTTP client):
```sh
curl -X POST http://localhost:5000/generate \
  -H "Content-Type: application/json" \
  -H "X-API-KEY: input-api-key-here" \
  -d '{"prompt": "A futuristic city skyline at sunset", "size": "1024x1024"}'
```

**Expected response**:
```json
{
  "image": "iVBORw0KGgoAAAANSUhEUgAA...",
  "filename": "1704115200_a3f5b2.png"
}
```

The image is automatically saved to the `images/` folder on the server.

### **Running the gRPC Server**

To run the gRPC server:

```sh
python grpc_server.py
```

The gRPC server will start on port `50051`. You should see:
```
gRPC Server started on port 50051
```

**Note**: Make sure the server stays running in this terminal window.

### **Testing with the gRPC Client**

Open a **new terminal window** (keep the gRPC server running in the first terminal), activate your virtual environment, and run:

```sh
python grpc_client.py
```

The client will:
1. Connect to the gRPC server at `localhost:50051`
2. Send a request with the prompt: "A futuristic city skyline at sunset"
3. Display the generated image data (base64 encoded) and the saved image path

**Expected output**:
```
Image Generated Successfully!
Base64 Image Data: iVBORw0KGgoAAAANSUhEUgAA...
Image saved as: images/1704115200_a3f5b2.png
```

**Note**: Generated images are automatically saved to the `images/` folder with a unique filename format: `{timestamp}_{hash}.{extension}`. The image format (PNG, JPG, etc.) is automatically detected from the image data.

**Note**: If you want to test with a different prompt, you can modify the `generate_image()` call at the bottom of `grpc_client.py` or call the function with custom parameters.

### **Testing with a Custom Prompt**

You can modify `grpc_client.py` to test with different prompts:

```python
if __name__ == "__main__":
    generate_image("Your custom prompt here", size="1024x1024")
```

**Available image sizes** for DALL·E 3: `1024x1024`, `1792x1024`, or `1024x1792`

---

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
    string image = 1;      // Base64 encoded image data
    string filename = 2;   // Saved filename (e.g., "1704115200_a3f5b2.png")
}

// Define the gRPC service
service ImageGenerationService {
    rpc GenerateImage (ImageRequest) returns (ImageResponse);
}
```

This schema defines the **ImageGenerationService** with a `GenerateImage` method that takes an `ImageRequest` (containing the prompt, image size, and API key) and returns an `ImageResponse` with both the generated image in base64 format and the saved filename.

For more information on how to define the request and response messages of a proto file i.e `Service Definition` please see the [protobuf documentation](https://protobuf.dev/) 

---

## **Image Saving Feature**

Both the REST API and gRPC server automatically save generated images to the `images/` folder. The implementation includes:

- **Automatic Image Saving**: All generated images are saved server-side with unique filenames
- **Format Detection**: Image format (PNG, JPG, GIF, WebP, BMP) is automatically detected from the binary data
- **Unique Naming**: Files are named using the format `{timestamp}_{hash}.{extension}` (e.g., `1704115200_a3f5b2.png`)
- **Error Handling**: If saving fails, the request still succeeds and returns the base64 data

The image saving functionality is implemented in `image_utils.py` using a shared utility function that both the Flask and gRPC servers use.

**REST API Response**:
```json
{
  "image": "iVBORw0KGgoAAAANSUhEUgAA...",
  "filename": "1704115200_a3f5b2.png"
}
```

**gRPC Response** includes both `image` (base64) and `filename` fields in the `ImageResponse` message.

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
from image_utils import save_base64_image

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
            return image_generation_pb2.ImageResponse(image="", filename="")

        if not request.prompt:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Prompt is required")
            return image_generation_pb2.ImageResponse(image="", filename="")

        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=request.prompt,
                n=1,
                size=request.size or "1024x1024",
                response_format="b64_json"
            )
            base64_image = response.data[0].b64_json
            
            # Save the image to the images folder
            filename = ""
            try:
                filename = save_base64_image(base64_image)
            except Exception as save_error:
                # If saving fails, log the error but still return the base64 data
                print(f"Warning: Failed to save image: {str(save_error)}")
            
            return image_generation_pb2.ImageResponse(
                image=base64_image,
                filename=filename
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return image_generation_pb2.ImageResponse(image="", filename="")

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

This code initializes a gRPC server, listens on port 50051, and handles image generation requests using OpenAI's API. After generating an image, it automatically saves it to the `images/` folder using the `save_base64_image()` utility function and returns both the base64 data and the saved filename.

---

## **Step 4: Implementing the gRPC Client**
To test the gRPC server, this is a simple client script in `grpc_client.py`:

```python
import os
import grpc
import image_generation_pb2
import image_generation_pb2_grpc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SERVER_ADDRESS = os.getenv("SERVER_ADDRESS")
API_KEY = os.getenv("API_SECRET_KEY")

def generate_image(prompt, size="1024x1024"):
    channel = grpc.insecure_channel(SERVER_ADDRESS)
    stub = image_generation_pb2_grpc.ImageGenerationServiceStub(channel)
    request = image_generation_pb2.ImageRequest(prompt=prompt, size=size, api_key=API_KEY)

    try:
        response = stub.GenerateImage(request)
        print("Image Generated Successfully!")
        print(f"Base64 Image Data: {response.image[:100]}...")
        
        # Display saved image path if filename is available
        if response.filename:
            images_dir = "images"
            image_path = os.path.join(images_dir, response.filename)
            print(f"Image saved as: {image_path}")
        else:
            print("Note: Image was not saved (no filename returned)")
    except grpc.RpcError as e:
        print(f"Error: {e.code()} - {e.details()}")

if __name__ == "__main__":
    generate_image("A futuristic city skyline at sunset")
```

This client connects to the gRPC server, sends an image generation request, and displays both the base64 data preview and the path where the image was saved on the server.

---

## **Final Thoughts**
The `grpc_client.py` can directly call the Image Generation method on the `grpc_server.py` application on a different machine as if it were a local object, making it efficient and easier to create a distributed application and service.

The benefits include:

- ✅ Faster request processing due to HTTP/2
- ✅ Reduced data overhead with Protocol Buffers
- ✅ Strongly typed contracts for better API structure
- ✅ Automatic image saving with unique filenames
- ✅ Format detection and proper file extension handling

If you’re building a distributed, high-performance API, consider making the switch to gRPC!

Let me know if you’ve done a similar migration—I’d love to hear your thoughts! 🚀

