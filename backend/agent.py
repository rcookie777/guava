import os
import json
from groq import Groq
from dotenv import load_dotenv
import requests
from langchain_core.tools import Tool
from langchain_google_community import GoogleSearchAPIWrapper
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch
import http
import urllib
from langchain_core.tools import tool

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

class Agent:
    def __init__(
        self,
        task,
        tools,
        agent_type,
        llm,
    ):
        self.task = task
        self.tools = tools
        self.llm = groq_client
        
        # print("RUNNING AGENT TASK: " + str(self.task) + "TOOLS: " + str(self.tools))
        for tool in self.tools:
            if tool == "search()":
                pass
            if tool == "get_orderbook()":
                pass

    def google_search(self,search: GoogleSearchAPIWrapper):
        tool = Tool(
            name="google_search",
            description="Search Google for recent results.",
            func=search.run,
        )

    def use_groq(self, system_prompt, prompt):
        chat_completion = self.llm.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            model="llama3-groq-70b-8192-tool-use-preview",
            # functions=[
            #     {
            #         "name": "get_weather",
            #         "description": "Get the current weather for a location",
            #         "parameters": {
            #             "type": "object",
            #             "properties": {
            #                 "location": {
            #                     "type": "string",
            #                     "description": "The city and state, e.g. San Francisco, CA"
            #                 },
            #                 "unit": {
            #                     "type": "string",
            #                     "enum": ["celsius", "fahrenheit"],
            #                     "description": "The unit of temperature to use. Defaults to fahrenheit."
            #                 }
            #             },
            #             "required": ["location"]
            #         }
            #     }
            # ],
            tool_choice="auto",
            max_tokens=4096,
        )

        return chat_completion.choices[0].message.content
    
    # Function to use LoRA fine-tuned model for text generation
    def use_lora(self, prompt):
        # Load the base model and tokenizer for LoRA
        model_name = "meta-llama/Llama-2-7b-hf"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16)

        # Load LoRA fine-tuned model
        peft_model_path = "fine_tuned"  # Replace with the path to your LoRA model files
        lora_model = PeftModel.from_pretrained(model, peft_model_path)

        # Move the model to GPU if available
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        lora_model.to(device)

        # Tokenize the prompt
        inputs = tokenizer(prompt, return_tensors="pt").to(device)

        # Generate a response
        output = lora_model.generate(
            inputs["input_ids"],
            max_new_tokens=150,
            do_sample=True,
            temperature=0.5,  # Adjust this as needed
            top_p=0.9,
        )

        # Decode the generated text
        generated_text = tokenizer.decode(output[0], skip_special_tokens=True).strip()

        # Remove the original prompt from the generated text
        generated_text = generated_text.replace(prompt, "").strip()



        # Ensure the output starts with "Answer:" as required
        if not generated_text.startswith("Answer:"):
            generated_text = "Answer: " + generated_text
        # Return the generated text
        return generated_text


    def generate_search_query(self, task_description):
        # Define a system prompt to instruct the LLM to generate the best search query
        system_prompt = """
        You are an expert search query generator. Your task is to generate the most effective search query for finding information online.
        Only provide a single-line search query based on the user's task description. Do not provide explanations, just the search query.
        """

        # Call the LLM to generate the search query
        query = self.llm.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": task_description},
            ],
            model="llama3-groq-70b-8192-tool-use-preview",
            max_tokens=50,  # Limit the token size to ensure concise queries
        )

        # Return the search query generated by the LLM
        return query.choices[0].message.content.strip()

    def extract_task_and_tools(self, response_content):
        response_json = json.loads(response_content)

        tasks = response_json.get("tasks", [])
        tools = response_json.get("tools", [])

        task_details = []
        for task in tasks:
            task_description = task.get("task", "No task description found")
            
            task_tools = task.get("tools", [])
            
            if not task_tools:
                task_tools = ["No tool found"]
            
            task_details.append({"description": task_description, "tools": task_tools})

        return task_details, tools

    def place_trade(self):
        pass

    def get_prediction_market_data(self):
        pass

    def researcher(self):
        pass

    def get_news_headlines(self, keywords=None, countries=None, categories=None, limit=10):
        conn = http.client.HTTPConnection("api.mediastack.com")
        params = urllib.parse.urlencode(
            {
                "access_key": os.getenv("MEDIA_STACK_API"),
                "limit": limit,
            }
        )

        conn.request("GET", "/v1/news?{}".format(params))
        res = conn.getresponse()
        data = res.read()

        decoded_data = data.decode("utf-8")
        news_data = json.loads(decoded_data)
        print(news_data)

        headlines = []
        for article in news_data.get("data", []):
            headline_info = {
                "headline": article.get("title"),
                "url": article.get("url"),
                "published_at": article.get("published_at"),
            }
            headlines.append(headline_info)

        conn.close()

        return headlines


if __name__ == "__main__":
    load_dotenv()
    print("Starting Agent")
    groq_client = Groq(
        api_key=os.getenv("GROQ_API_KEY"),
    )

    # headlines = agent.get_news_headlines()

    polymarket_market = {
        "source": "Polymarket",
        "market_id": "0x1f5f0d3a3662423d9f24d46b001f1de4e4dcd4f3c0e200d45c1c23e87b503c29",
        "status": "Active",
        "headline": "Will the Democratic candidate win Pennsylvania by 0.5%-1%?",
        "description": 'This market will resolve to "Yes” if the Democratic Party candidate wins the popular vote in Pennsylvania in the 2024 U.S. Presidential Election by between 0.5% (inclusive) and 1% (exclusive) or more when compared with the second place candidate. Otherwise, this market will resolve to "No".\n\nFor the purpose of resolving this market, the \'margin of victory\' is defined as the absolute difference between the percentages of votes received by the Democratic Party candidate and the second-place candidate. Percentages of the votes received by each party will be determined by dividing the total number of votes each of the top two candidates receives by the sum of all votes cast in Pennsylvania for the 2024 U.S. Presidential Election.\n\nThis market will resolve based off the official vote count once Pennsylvania has certified the vote. \n\nIf a recount is initiated before certification, the market will remain open until the recount is completed and the vote is certified. If a recount occurs after certification, the recount will not be considered.',
        "end_date": "2024-11-05T12:00:00Z",
        "yes_ask": 0.065,
        "no_ask": 0.935,
        "liquidity": 35388.2459,
    }

    master = Agent("", "",llm=groq_client,agent_type='master')
    prompt = "Can you explain the concept of monopsony in economics?"
    response = master.use_lora(prompt)
    print(response)
    # search = GoogleSearchAPIWrapper(google_api_key=os.getenv('GOOGLE_API_KEY'),google_cse_id=os.getenv('GOOGLE_CSE_ID'))
    # master.google_search(search)
    # headlines = [
    #     {
    #         "headline": "Tristan Matthews’ late field goal lifts Central Michigan over San Diego State 22-21",
    #         "url": "https://www.mymotherlode.com/sports/college-sports-general-news/3432631/tristan-matthews-late-field-goal-lifts-central-michigan-over-san-diego-state-22-21.html",
    #         "published_at": "2024-09-29T00:12:53+00:00",
    #     },
    #     {
    #         "headline": "El Papa Francisco advierte a todos que el fin del mundo se acerca",
    #         "url": "https://mundonow.com/el-papa-francisco-advierte-que-el-fin-del-mundo-se-acerca/",
    #         "published_at": "2024-09-29T00:12:41+00:00",
    #     },
    #     {
    #         "headline": "Hajj-Malik Williams guides unbeaten UNLV to 59-14 romp over Fresno State",
    #         "url": "https://www.mymotherlode.com/sports/college-sports-general-news/3432630/hajj-malik-williams-guides-unbeaten-unlv-to-59-14-romp-over-fresno-state.html",
    #         "published_at": "2024-09-29T00:12:26+00:00",
    #     },
    #     {
    #         "headline": "Lumsden, Sask. welcomes visitors for annual Scarecrow Festival",
    #         "url": "https://globalnews.ca/news/10784711/lumsden-sask-welcomes-visitors-scarecrow-festival/",
    #         "published_at": "2024-09-29T00:12:08+00:00",
    #     },
    #     {
    #         "headline": "Nahost-Liveblog: ++ Iran fordert Sitzung des UN-Sicherheitsrats ++",
    #         "url": "https://www.tagesschau.de/newsticker/liveblog-nahost-sonntag-190.html",
    #         "published_at": "2024-09-29T00:12:01+00:00",
    #     },
    #     {
    #         "headline": "Truman's Deployment [Image 10 of 11]",
    #         "url": "https://www.dvidshub.net/image/8667553/trumans-deployment",
    #         "published_at": "2024-09-29T00:11:58+00:00",
    #     },
    #     {
    #         "headline": "Truman's Deployment [Image 11 of 11]",
    #         "url": "https://www.dvidshub.net/image/8667554/trumans-deployment",
    #         "published_at": "2024-09-29T00:11:58+00:00",
    #     },
    #     {
    #         "headline": "Truman's Deployment [Image 9 of 11]",
    #         "url": "https://www.dvidshub.net/image/8667546/trumans-deployment",
    #         "published_at": "2024-09-29T00:11:58+00:00",
    #     },
    #     {
    #         "headline": "Truman's Deployment [Image 8 of 11]",
    #         "url": "https://www.dvidshub.net/image/8667545/trumans-deployment",
    #         "published_at": "2024-09-29T00:11:57+00:00",
    #     },
    #     {
    #         "headline": "Truman's Deployment [Image 6 of 11]",
    #         "url": "https://www.dvidshub.net/image/8667542/trumans-deployment",
    #         "published_at": "2024-09-29T00:11:57+00:00",
    #     },
    # ]
    # master_response = master.use_groq(system_prompt=MASTER_PROMPT,prompt=polymarket_market['headline'])
    # print("MASTER RESPONSE:" + master_response)
    # task_details, tools = master.extract_task_and_tools(master_response)
    # sub_agents = []
    # print("Number of tasks generated: ", len(task_details))

    # # for i, task in enumerate(task_details):
    # #     print(f"Task {i+1}: {task['description']}")
    # #     print(f"Number of tools for Task {i+1}: {len(task['tools'])}")
    # #     print(f"Tools for Task {i+1}: {task['tools']}")
    # for task in task_details:
    #     description = task['description']
    #     task_tools = task['tools']
    #     agent = Agent(description, task_tools, agent_type="sub-agent", llm=groq_client)
    #     sub_agents.append(agent)


    task_description = "Search for recent political polls and trends in Pennsylvania."

    # Call the function to generate the search query
    search_query = master.generate_search_query(task_description)

    print("Generated Search Query:", search_query)