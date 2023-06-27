from flask import Flask, request, jsonify, render_template
import requests
import mysql.connector
import json
import re 
import os
import datetime

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv()) 
from langchain import OpenAI, SQLDatabase, SQLDatabaseChain
from langchain.prompts.prompt import PromptTemplate

_DEFAULT_TEMPLATE = """Given an input question, first create a syntactically correct {dialect} query to run, then look at the results of the query and return the answer.
RULES:
Make the query/sql result have comparation data so it can be used by another ai to build a chart of that data also always to put date, name of the field or target description, summary data for the charts. 
if the user want yearly data then make the output summary of each year as representatif of the data, 
if the user want monthly data then make the output summary of Months on current/spesific year data, 
if the user want daily data then make it the output summary on each day on current/spesific month data,
and if the user only want the spesific top data then output it like so.

IMPORTANT : Make SURE TO INCLUDE date, name of the field or target description, summary data on query select for the charts in the query base on the user intent

based on SQLResult output answer as : 
1. analyze the data and the user want
2. Based on the analyze and the data sources generate data with csv format table for the data
3. output the csv data on the answer with the field name

Only use the following tables:
{table_info}

Question: {input}"""
PROMPT = PromptTemplate(
    input_variables=["input", "table_info", "dialect"], template=_DEFAULT_TEMPLATE
)
# SQLDatabase()
# db = SQLDatabase.from_uri("sqlite:///../../../../notebooks/Chinook.db")
# llm = OpenAI(temperature=0, verbose=True)

database_md=""
app = Flask(__name__)

def create_chat_completion(system,user,model):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer '+"catto_key_GWV8czjyQBmvmbUGfBjpll3q"
    }
    params = {
        "model": model, #"claude-instant-100k"
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.7, 
    }
    response=""
    try:
        response = requests.post("https://api.catto.tech/v1/chat/completions", json=params, headers=headers)
    except:
        print(params)
    result = response.json()
    hasil= result['choices'][0]['message']['content']
    return hasil

@app.route('/', methods=['GET'])
def index():
    return os.getenv("html")

query_generator="""Follow the following instructions:
INSTRUCTION
User Input : {prompt}
Here is the data table source : 
{docs}

Mission: Create a complex SQL query that can represent an analyst data display in the form of a coolest lookin chart.

Step:

1. Analyze the relationships between the tables.
2. Create a complex VERBOSE MySQL query that can be used by another AI to build an ApexChart based on the data,
  If the user wants yearly data, generate a query to output of each year's data,
  If the user wants monthly data, generate a query to output of each month within the current/specific year's data,
  If the user wants daily data, generate a query to output of each date day within the current/specific month's data,
  If the user only wants specific top data then dont make it verbose dont limit the selection,
  and always to group by the data so it output more data.
3. Output an SQL query.


format response :
sql query

IMPORTANT :
1. only show the output result of step 3 as sql query.
2. do not explain the step just straight up to the format response.
3. Always Include to select an item description as part of select field.
4. MAKE SURE TO ADD ; ON THE VERY END OF QUERY.
5. if select target name make sure to use LIKE "%<target>%"
6. if you need to select multiple target then or/and on where target
"""

data_series_generator="""
Follow the following instructions:
INSTRUCTION
User Input : {prompt}
Here is the data source : 
{docs}

Step :
1. Based on data source and the user want generate an option data for a chart with apexchart.js, 
if you want to label the data then put it on the name series instead of y axis DO NOT use formatter or make function on y axis .
if the value is Null or None output it with 0 or " " .
make sure to add all the data value
2. Decide the chart type, distinct colors, title, label (without formatter), xaxis,yaxis.
3. output the option as json string that compatible with json.loads() 


format response :
json string

IMPORTANT :
1. only show the output result of step 2 as json string 
2. do not explain the step just straight up to the format response
3. Make SURE DO NOT include any comments or unnecessary explanation
"""


data_series_generator2="""
Follow the following instructions:
INSTRUCTION
User Input : {prompt}
Here is the data source : 
{docs}

Step :
1. Based on data source and the user want generate an option data for a chart with apexchart.js and Decide the coolest type chart that suitable for the case user want
2. if it requires drawing a line/area/bar Chart, reply as follows:
{
  "chart":{ "type": "<Chart_type>","height":400 },
   "toolbar": {
    "show": true,
    "tools": {
      "zoom": true,
    },
  },
  "zoom": {
    "enabled": true,
  },
  "title": { "text": "Chart Title" },
  "series": [
    {
      "name": "Series 1",
      "data": [value1, value2, ...]
    },
    {
      "name": "Series 2",
      "data": [value1, value2, ...]
    },
    ...
  ],
  "xaxis": {
    "categories": ["A","B","C",...]
  },
  "yaxis": {
    "title": {
      "text": "<title>"
    }
    ...
  },
}

If the query requires creating a pie/donut/polarArea/radialBar chart, reply as follows:
{
  "chart":{ "type": "<Chart_type>","height":400 },
  "title": { "text": "Chart Title" },
  "series": [value1, value2, ...],
  "labels": ["A", "B", "C", ...]
};


If the query requires creating a radar chart, reply as follows:
{
  "chart":{ "type": "<Chart_type>","height":400 },
  "title": { "text": "Chart Title" },
  "series": [
    {
      "name": "Series 1",
      "data": [value1, value2, ...]
    },
    {
      "name": "Series 2",
      "data": [value1, value2, ...]
    },
    ...
  ],
  "labels": ["A", "B", "C", ...]
}

If the query requires creating a scatter/treemap chart, reply as follows:
{
  "chart":{ "type": "<Chart_type>","height":400 },
  "title": { "text": "Chart Title" },
  "series": [
    {
      "name": "Series 1",
      "data": [
        { "x": "name of value", "y": val1 },
        { "x": "name of value", "y": val2 },
        ...
      ]
    }
  ]
}

If the query requires creating a candlestick chart, reply as follows:
{
  "chart":{ "type": "<Chart_type>","height":400 },
  "title": { "text": "Chart Title" },
  "series": [
    {
      "name": "Series 1",
      "data": [
        { "x": datetime.datetime.fromtimestamp(timestamp), "y": [val1, val2, ...] },
        { "x": datetime.datetime.fromtimestamp(timestamp), "y": [val1, val2, ...] },
        ...
      ]
    }
  ]
}

There can only be 8 types of chart, line/area/bar/pie/donut/radar/scatter/polarArea/radialBar/treemap/candlestick Chart
as for a combination of chart like  bar and line use your own knowledge to make the output.

DO NOT ADD 
"tooltip": {
    "y": {
      "formatter": function (val) {
      }
    }
  }

3. output the option as json string that compatible with json.loads() 


format response :
json string

IMPORTANT :
1. only show the output result of step 3 as json string 
2. do not explain the step just straight up to the format response
3. Make SURE DO NOT include any comments or unnecessary explanation
4. DO NOT USE a FUNCTION format or callback on the data output because it will be stringify
5. Enable toolbar on the chart 
"""

@app.route('/create-chart1', methods=['POST'])
def create_chart1():
    global query_generator
    data = request.get_json()
    database_name = data['database']
    prompt = data['prompt']
    connection = connect_to_database(database_name)
    database_details = extract_database_details(connection)
    database_md=database_details
    query_generator=query_generator.replace("{docs}",database_md).replace("{prompt}",prompt)
    output=create_chat_completion(query_generator,prompt,'gpt-3.5-turbo-16k')
    print(output)
    output_query=output
    output = output[output.index("SELECT"):output.rindex(";")+1]
    print('-----------------------output-----------------------')
    print(output)
    result = query_db(connection,output)
    print('-----------------------result-----------------------')
    print(result['csv'])
    # # dbc.save_to_file(database_name, database_details)
    # data_series=data_series_generator.replace("{docs}",result).replace("{prompt}",prompt)
    data_series2=data_series_generator2.replace("{docs}",result['csv']).replace("{prompt}",prompt)
    output2=create_chat_completion(data_series2,prompt,'gpt-3.5-turbo-16k')
    print('series 2')
    obj = output2[output2.index("{"):output2.rindex("}")+1]
    print(type(obj))
    print(obj)
    # output=create_chat_completion(data_series,prompt,'gpt-4')
    # print(type(output))
    # print(output)
    return jsonify({"message":json.loads(output2),"query":output_query,"datanya":result['json']})

@app.route('/create-chart2', methods=['POST'])
def create_chart2():
    data = request.get_json()
    database_name = data['database']
    dburi = f"mysql+pymysql://root:@localhost/{database_name}"
    db = SQLDatabase.from_uri(dburi)
    llm = OpenAI(temperature=0)
    db_chain = SQLDatabaseChain.from_llm(llm=llm, db=db, top_k=1,return_direct=True, use_query_checker=True,prompt=PROMPT)
    # return_intermediate_steps=True,
    prompt = data['prompt']
    result=db_chain(prompt)
    print(type(result))
    print(result)
    data_series=data_series_generator.replace("{docs}",json.dumps(result['result'])).replace("{prompt}",prompt)
    output=create_chat_completion(data_series,prompt)
    print(output)
    output=json.loads(output)
    # list_data=result["intermediate_steps"][3]
    # text=result["intermediate_steps"][5]
    # print(text)
    return jsonify({"message":output})


def extract_string_between(text, start_delimiter, end_delimiter):
    start_index = text.find(start_delimiter)
    if start_index == -1:
        return None

    start_index += len(start_delimiter)
    end_index = text.find(end_delimiter, start_index)
    if end_index == -1:
        return None

    return text[start_index:end_index]

def find_json_strings(text):
    json_strings = re.findall(r'({.*?})', text)
    valid_json_strings = []
    for json_str in json_strings:
        try:
            json_obj = json.loads(json_str)
            valid_json_strings.append(json_str)
        except json.JSONDecodeError:
            pass
    return valid_json_strings

def connect_to_database(database_name):
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database=database_name
    )
    return connection

def query_db(connection,query):
    cursor = connection.cursor()
    cursor.execute(query)
    column_names = [column[0] for column in cursor.description]
    table_data = cursor.fetchall()

    # column_names = [desc[0] for desc in cursor.description]
    data = []
    for row in table_data:
        row_data = {}
        for column_name, value in zip(column_names, row):
            row_data[column_name] = str(value)
        data.append(row_data)
    json_data = json.dumps(data)
    output=""
    output=output+",".join(column_names)+"\n"
    for x in table_data:
        list_data = [str(element) for element in x]
        output=output+",".join(list_data)+"\n"
    return {"csv":output,"json":json_data}

def extract_database_details(connection):
    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    database_details = []
    database_md=""
    for table in tables:
        table_name = table[0]
        database_md=database_md+f"#{table_name}\n"
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = cursor.fetchall()
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
        example_data = cursor.fetchone()
        fields = []
        f_name = []
        f_value = []
        for i, column in enumerate(columns):
            field_name, field_type, _, _, _, extra = column
            property = "(primary)" if extra == "auto_increment" else ""
            fields.append({
                "field_name": field_name,
                "type_field": field_type + property,
                "example_data": str(example_data[i]) if example_data else ""
            })
            f_name.append(field_name)
            f_value.append(str(example_data[i]) if example_data else "")
        database_md=database_md+",".join(f_name)+"\n"
        database_md=database_md+",".join(f_value)+"\n"
        database_details.append({
            "table": table_name,
            "list_fields": fields
        })
    return database_md

def save_to_file(database_name, data):
    with open(f"{database_name}.json", "w") as file:
        json.dump(data, file, indent=2)

if __name__ == '__main__':
    app.run(port=5001,debug=True)