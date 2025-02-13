import os
import grpc
import openai
from concurrent import futures
import image_generation_pb2
import image_generation_pb2_grpc
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in environment variables")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Implement the gRPC Service
class ImageGenerationService(image_generation_pb2_grpc.ImageGenerationServiceServicer):
    def GenerateImage(self, request, context):
        # Authentication Check
        if request.api_key != os.getenv("API_SECRET_KEY"):
            context.set_code(grpc.StatusCode.PERMISSION_DENIED)
            context.set_details("Invalid API key")
            return image_generation_pb2.ImageResponse(image="")

        # Validate Prompt
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
