import torch
from fastapi import FastAPI
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# Initialize FastAPI app
app = FastAPI()

# Load the base model and tokenizer
model_name = "meta-llama/Llama-2-7b-hf"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16)

# Load LoRA fine-tuned model
peft_model_path = "nice"  # Replace with the path to your LoRA model files
lora_model = PeftModel.from_pretrained(model, peft_model_path)

# Move the model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
lora_model.to(device)

# Define a request body structure
class PromptRequest(BaseModel):
    prompt: str

# API route to generate text based on the input prompt
@app.post("/generate/")
async def generate_text(request: PromptRequest):
    prompt = request.prompt
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    output = lora_model.generate(
        inputs["input_ids"],
        max_new_tokens=100,
        do_sample=True,
        temperature=0.7
    )
    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
    return {"generated_text": generated_text}

