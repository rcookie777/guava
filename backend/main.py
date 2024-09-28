from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  

from news import DataItem, NewsItem
from agent import AgentTask

data_items = [
    DataItem(name='Market A', value='Up 2%'),
    DataItem(name='Market B', value='Down 1%'),
]

agent_tasks = [
    AgentTask(task='Analyze Market A', status='Completed'),
    AgentTask(task='Predict Market B', status='In Progress'),
]

news_items = [
    NewsItem(title='Market A Hits Record High', url='https://news.example.com/market-a'),
    NewsItem(title='Economic Outlook for Q4', url='https://news.example.com/q4-outlook'),
]

@app.route('/api/data', methods=['GET'])
def get_data():
    return jsonify([item.to_dict() for item in data_items])

@app.route('/api/agent-tasks', methods=['GET'])
def get_agent_tasks():
    return jsonify([task.to_dict() for task in agent_tasks])

@app.route('/api/news', methods=['GET'])
def get_news():
    return jsonify([news.to_dict() for news in news_items])

if __name__ == '__main__':
    app.run(debug=True)
