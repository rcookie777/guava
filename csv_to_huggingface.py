import pandas as pd
from datasets import Dataset
from huggingface_hub import HfApi, login

# Step 1: Load CSV into a pandas DataFrame
df = pd.read_csv('formatted_conversations.csv')

# Step 2: Convert DataFrame to Hugging Face Dataset
dataset = Dataset.from_pandas(df)

# Step 3: Save the dataset locally to verify structure (Optional)
dataset.save_to_disk('formatted_conversations_dataset')

# Step 4: Log in to Hugging Face (Make sure you've logged in via CLI)
#login()

# Step 5: Create a new dataset repository programmatically
api = HfApi()

# Provide your Hugging Face username and dataset name
username = "YungCarti"
repo_name = "guava"

# Create the new dataset repository
repo_id = f"{username}/{repo_name}"
#api.create_repo(repo_id=repo_id, repo_type="dataset", exist_ok=True)

# Step 6: Push dataset to the newly created repository on Hugging Face Hub
dataset.push_to_hub(repo_id)

print(f"Dataset pushed to Hugging Face Hub: https://huggingface.co/datasets/{repo_id}")
