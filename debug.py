import pandas as pd
from huggingface_hub import login, HfApi
from datasets import Dataset

# Step 1: Load the CSV file
fp = 'formatted_conversations.csv'
df = pd.read_csv(fp)

# Step 2: Display the columns to check the structure
print(df.columns)

# Step 3: Convert the pandas DataFrame to a Hugging Face Dataset
# Ensure the DataFrame has the correct structure (e.g., it contains a 'text' column)
dataset = Dataset.from_pandas(df)

# Check the dataset structure
print(dataset)

# Step 4: Save the dataset locally
dataset.save_to_disk('formatted_conversations_dataset')

# Step 5: Login to Hugging Face
#login()

# Step 6: Create a new dataset repository on Hugging Face and push the dataset
api = HfApi()

# Push the dataset to Hugging Face Hub
dataset.push_to_hub("YungCarti/formatted_conversations")
