import torch
from PIL import Image
from transformers import AutoModelForVision2Seq, AutoProcessor
import json
import os
import cv2
import config.settings as settings

# Initialize model variables as None
qwen_model = None
qwen_processor = None

def load_qwen_model():
    """
    Load the Qwen2 model and processor if not already loaded
    """
    global qwen_model, qwen_processor
    
    try:
        if qwen_model is None or qwen_processor is None:
            # Set device
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Define model path
            model_path = "models/Qwen2-VL-2B-OCR-fp16"
            
            # Load processor
            print("Loading processor...")
            qwen_processor = AutoProcessor.from_pretrained(
                model_path, 
                size={"shortest_edge": 56 * 56, "longest_edge": 28 * 28 * 1280}
            )
            
            # Load model
            print("Loading model...")
            qwen_model = AutoModelForVision2Seq.from_pretrained(
                model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto",
                trust_remote_code=True
            )
            
            return {"status": "success", "message": "Model loaded successfully"}
        else:
            return {"status": "success", "message": "Model already loaded"}
    except Exception as e:
        print(f"Error loading model: {str(e)}")
        return {"status": "error", "message": f"Failed to load model: {str(e)}"}

def process_document(image_path):
    """
    Process a document using the Qwen2 model
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        dict: Extracted information from the document
    """
    global qwen_model, qwen_processor
    
    try:
        # Check if model is loaded
        if qwen_model is None or qwen_processor is None:
            return {"ERROR": "Qwen2 model not loaded. Please load the model first."}
        
        # Check if image exists
        if not os.path.exists(image_path):
            return {"ERROR": "Image file not found."}
        
        # Load and process image
        try:
            pil_image = Image.open(image_path).convert("RGB")
            pil_image = pil_image.resize((640, 640))
        except Exception as e:
            return {"ERROR": f"Failed to process image: {str(e)}"}
        
        # Prompt for entity extraction
        prompt_text = """Extract NAME, ORG, DES, PHONE, EMAIL, WEB from the image. Respond as JSON. Only use visible info.
{
  "NAME": [],
  "ORG": [],
  "DES": [],
  "PHONE": [],
  "EMAIL": [],
  "WEB": []
}"""
        
        # Create conversation
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": pil_image},
                    {"type": "text", "text": prompt_text}
                ]
            }
        ]
        
        # Process inputs
        try:
            prompt = qwen_processor.apply_chat_template(conversation, add_generation_prompt=True)
            inputs = qwen_processor(
                text=[prompt],
                images=[pil_image],
                padding=True,
                return_tensors="pt"
            ).to(qwen_model.device)
        except Exception as e:
            return {"ERROR": f"Failed to process model inputs: {str(e)}"}
        
        # Generate output
        try:
            with torch.no_grad():
                output_ids = qwen_model.generate(
                    **inputs,
                    max_new_tokens=512,
                    do_sample=False,
                    num_beams=1,
                    early_stopping=True
                )
            
            # Decode output
            generated_text = qwen_processor.batch_decode(output_ids, skip_special_tokens=True)[0]
        except Exception as e:
            return {"ERROR": f"Error in model generation: {str(e)}"}
        
        # Handle empty response
        if not generated_text or len(generated_text.strip()) == 0:
            return {"ERROR": "The AI model returned an empty response."}

        # Extract JSON from response
        try:
            # Find JSON-like content in the response
            start_idx = generated_text.find('{')
            end_idx = generated_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                return {"ERROR": "No valid JSON found in response"}
            
            json_str = generated_text[start_idx:end_idx]
            results = json.loads(json_str)
            
            # Ensure all required keys are present
            for key in ["NAME", "ORG", "DES", "PHONE", "EMAIL", "WEB"]:
                if key not in results:
                    results[key] = []
            
            return results
            
        except json.JSONDecodeError as e:
            return {"ERROR": f"Failed to parse JSON response: {str(e)}"}
        except Exception as e:
            return {"ERROR": f"Error processing model response: {str(e)}"}
            
    except Exception as e:
        return {"ERROR": f"Unexpected error in document processing: {str(e)}"} 