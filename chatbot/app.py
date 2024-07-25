from flask import Flask, request, jsonify, render_template
import openai
import json
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app) 

api_key = "YOUR OPENAI SECRECT KEY"
openai.api_key = api_key

def get_us_population(year):
    response = requests.get(f"https://datausa.io/api/data?drilldowns=Nation&measures=Population&year={year}")
    data = response.json()
    population_data = next((item for item in data["data"] if item["Year"] == str(year)), None)
    return population_data

def get_state_population(state, year):
    response = requests.get(f"https://datausa.io/api/data?drilldowns=State&measures=Population&year={year}")
    data = response.json()
    population_data = next((item for item in data["data"] if item["Year"] == str(year) and item["State"] == state), None)
    return population_data

def ask_openai(question):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[
            {"role": "user", "content": question}
        ],
        functions=[
            {
                "name": "get_us_population",
                "description": "Get the US population data for a specific year",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "year": {
                            "type": "integer",
                            "description": "The year for which to retrieve the population data"
                        }
                    },
                    "required": ["year"],
                },
            },
            {
                "name": "get_state_population",
                "description": "Get the population data for a specific state and year",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "state": {
                            "type": "string",
                            "description": "The name of the state"
                        },
                        "year": {
                            "type": "integer",
                            "description": "The year for which to retrieve the population data"
                        }
                    },
                    "required": ["state", "year"],
                },
            },
        ],
        function_call="auto"
    )
    
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data['question']
    
    response = ask_openai(question)

    if response['choices'][0]['finish_reason'] == "function_call":
        function_call = response['choices'][0]['message']['function_call']
        if function_call['name'] == "get_us_population":
            arguments = json.loads(function_call['arguments'])
            year = arguments['year']
            population_data = get_us_population(year)
            if population_data:
                answer = f"The population of the United States in {population_data['Year']} was {population_data['Population']}."
            else:
                answer = f"No population data found for the year {year}."
        elif function_call['name'] == "get_state_population":
            arguments = json.loads(function_call['arguments'])
            state = arguments['state']
            year = arguments['year']
            population_data = get_state_population(state, year)
            if population_data:
                answer = f"The population of {state} in {population_data['Year']} was {population_data['Population']}."
            else:
                answer = f"No population data found for {state} in the year {year}."
        else:
            answer = "Function call not recognized."
    else:
        answer = response['choices'][0]['message']['content']

    return jsonify({"response": answer})

if __name__ == "__main__":
    app.run(debug=True)
