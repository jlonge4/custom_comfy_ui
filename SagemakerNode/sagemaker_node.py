import boto3
import json
import base64
import io
from PIL import Image
import numpy as np
import torch

runtime = boto3.client('runtime.sagemaker')

class Text2ImageNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {"prompt": ("STRING", {"default": ""}), 
                         "strength": ("FLOAT", {"default": 0.75})}
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "image_to_image"
    CATEGORY = "image"
    OUTPUT_NODE = True

    def image_to_image(self, prompt):
        payload = json.dumps({"prompt": prompt})

        # Make the direct call
        response = runtime.invoke_endpoint(
            EndpointName="flux-image-generator-endpoint",
            ContentType="application/json",
            Body=payload
        )

        try:
            # Process response and convert to tensor
            json_response = json.loads(response)
    
            # Extract the base64-encoded image
            base64_img = json_response["image"]
            
            # Decode the base64 string
            img_bytes = base64.b64decode(base64_img)
            
            # Create a BytesIO object from the decoded bytes
            img_buffer = io.BytesIO(img_bytes)
            
            # Open the image using PIL
            img = Image.open(img_buffer)
            img.save("output_image.png")
            # Convert to numpy array with correct shape for save_images
            output_array = np.array(img)
            if len(output_array.shape) == 2:
                output_array = np.stack([output_array] * 3, axis=-1)
            
            # Convert to float32 and normalize to 0-1 range
            output_array = output_array.astype(np.float32) / 255.0
            
            # Create tensor in format expected by save_images: [B, H, W, C]
            output_tensor = torch.from_numpy(output_array)
            if len(output_tensor.shape) == 3:
                output_tensor = output_tensor.unsqueeze(0)  # Add batch dimension
            
            return (output_tensor,)

        except Exception as e:
            print(f"Error: {e}")


NODE_CLASS_MAPPINGS = {"Text2ImageNode": Text2ImageNode}
