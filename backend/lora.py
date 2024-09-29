import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

MASTER_PROMPT = """
    You are the master agent responsible for researching headlines and market data to inform predictions for platforms like Polymarket. Your goal is to gather relevant information and analyze trends to provide insights for prediction market outcomes.
    Capabilities:
    Spawn 2 sub-agents to assist in a research task.
    Use search() tool to find relevant news and information
    Use get_order_data() tool to retrieve market order data
    Task Management:
    Assess the given prediction market question or topic
    Determine key areas requiring research
    Spawn sub-agents as needed, assigning specific research tasks
    Analyze information gathered by sub-agents
    Synthesize findings into a concise prediction report
    Sub-Agent Spawning (Only spawn 2 tasks at a time):
    To spawn a sub-agent, use the following format:
    text
    Respond in JSON with no spacing.
    OUTPUT FORMAT:
    {
        tasks: [
            {"task": "Detailed description of the research task", 
            "tools": ["List of tools the agent can use e.g. search(), get_order_data()"]}
        ]
    }

    EXAMPLE OUTPUT:
    {
        tasks: [
            {"task": "Search for recent political polls and trends in Pennsylvania.", 
            "tools": ["search()"]}, 
            {"task": "Retrieve the latest market order data related to the Pennsylvania election.", 
            "tools": ["get_order_data()"]}
        ]
    }
    """

# Load the base model and tokenizer
model_name = "meta-llama/Llama-2-7b-hf"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16)

# Load LoRA fine-tuned model
peft_model_path = "fine_tuned"  # Replace with the path to your LoRA model files
lora_model = PeftModel.from_pretrained(model, peft_model_path)

# Move the model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
lora_model.to(device)

def generate_text(prompt: str) -> str:
    # Tokenize the prompt
    prompt = MASTER_PROMPT + prompt
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    
    # Generate text using the model
    output = lora_model.generate(
        inputs["input_ids"],
        max_new_tokens=512,  # Adjust based on your desired length      # Enable sampling for more creative outputs
        temperature=0.5,      # Adjust temperature for randomness in generation
        top_k=50,             # Adjust top_k for diversity in generation
    )
    
    # Decode the generated tokens to text
    generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
    
    return generated_text

# prompt = "How likely is the stock market to crash in 2022?"
# generated_text = generate_text(prompt)
# print(generated_text)