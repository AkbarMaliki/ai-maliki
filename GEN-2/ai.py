import openai
import webbrowser
import json
import os
from dotenv import load_dotenv
from langchain.tools import DuckDuckGoSearchRun
from langchain.embeddings.openai import OpenAIEmbeddings
browser = DuckDuckGoSearchRun()
import shutil
import re
from langchain.vectorstores import FAISS
# from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import ToMarkdownLoader
from langchain.document_loaders import CSVLoader
from langchain.document_loaders import TextLoader
from langchain.document_loaders import PyPDFLoader
from langchain.document_loaders import PlaywrightURLLoader
from langchain.document_loaders import UnstructuredExcelLoader
from langchain.document_loaders import UnstructuredPowerPointLoader
from langchain.document_loaders import UnstructuredWordDocumentLoader
import mysql.connector
import tiktoken


# GLOBAL VARIABLES
load_dotenv()
openai.api_base = os.getenv("openai_api_base")
openai.api_key = os.getenv("openai_api_key")
selection="5"
directory="generated"
openai_model="gpt-4-0613"
temperature=0.5
ignore=["pycache", "package","node_modules", "vendor",'wwebjs_auth','backup','.env','.md']
user_query=""
listpath=[]
messages=[]
document_db=[]
walk_code = ''
docs = ''
langchain_or_text=True
k=20
connection=""
thetoken=0


function_descriptions = [
    { "name": "function_schemas_generator", "description": """to generate chatgpt function schemas with all the properties type,description,required,enum,etc.  example : {"name":"control_light","description":"function to Turn on/off the light","parameters":{"type": "object", "properties": {"state": {"type": "string", "description": "the state of the light, should be on or off",enum:["on","off"]}}, "required": ["code", "filepath"]}}} note the properties here is the output from the function schema not the input. """, "parameters": {"type": "object","properties": { "function_schemas": {     "type": "string",     "description": "string with all the function_schemas data in json schemas format ", },},"required": ["function_schemas","next_process","decision"] } },
    {"name" : "create_app_or_game_project", "description":"""to create new app projects""","parameters":{"type":"object","properties":{"output":{"type":"string","description":"list of core function, rules, and classes. example : core functionality to - add new todos, - mark todos as complete, - remove todos"},"user_input":{"type":"string","description":"Improve version of user input"},"ui_properties":{"type":"string","description":"Information about how ui looks like primary color,secondary color,height,width,position, theme(Sci-Fi/Futuristic,Cyberpunk,Steampunk,Neon,Material Design,Flat Design,Skeuomorphic,Retro/Vintage,Grunge,Metro,Gothic,Cartoon/Comic,Industrial,Nature/Environmental,Abstract,Elegant). Always put theme as output"},"core":{"type":"string","description":"information about core function, classes, method and etc"}},"required":["output","user_input","ui_properties","core"]}},
    {"name": "create_plain_code","description":"to create only a plain code","parameters":{"type":"object","properties":{"code":{"type":"string","description":"The plain code to be created"}},"required":["code"]}},
    {"name":"improve_or_fix_provided_code","description":"to improve or fix existing code","parameters":{"type": "object", "properties": {"user_request": {"type": "string", "description": "Summary what user want"}}, "required": ["user_request"]}},
    {"name": "reset_memory","description": "to reset the memory of the ChatGPT chat messages.","parameters": {"type": "object","properties": {"confirm": {"type": "boolean","description": "A boolean flag to confirm the reset operation."}},"required": ["confirm"]}},
    {"name":"scan_and_read_directory","description":"to walk or scan through a directory, read all the files, and return a list containing the content of all files along with their file paths","parameters":{"type":"object","properties":{"directory":{"type":"string","description":"The path to the directory to be scanned"}},"required":["directory"]},"returns":{"type":"array","items":{"type":"object","properties":{"filepath":{"type":"string","description":"The file path"},"content":{"type":"string","description":"The content of the file"}}},"description":"List of files content and their respective file path from the directory"}},
    {"name":"critically_reflect_chatgpt_response","description":"to give a critical reflection on the previous response by ChatGPT assistant and list out possible mistakes, omissions, errors that need to be fixed and provide feedback for room for improvement.","parameters":{"type": "object", "properties": { "mistakes": {"type": "array", "items": {"type": "string"}, "description": "List of all possible mistakes in the previous response.", "default": []},"possible_error": {"type": "array", "items": {"type": "string"}, "description": "List of all possible error in the previous response that make the code not working as intented.", "default": []}, "omissions": {"type": "array", "items": {"type": "string"}, "description": "List of all possible omissions in the previous response.", "default": []}, "feedback": {"type": "string", "description": "Feedback for room for improvement."}}, "required": ["mistakes","possible_error","feedback","omissions"]}},
    { "name": "duck_go_browser_search", "description":"to search the web using DuckDuckGo search engine","parameters":{"type":"object","properties":{"query":{"type":"string","description":"The search query","minLength":1}},"required":["query"]}},
    {"name":"get_or_extract_scrapping_info_from_url","description":"to get/extract/scrapping information from the url that user provided","parameters":{"type": "object", "properties": {"url": {"type": "string", "description": "the url from which information is to be fetched","format":"uri"}}, "required": ["url"]}},
    {"name":"extract_url_as_markdown","description":"to get/extract/scrapping url as markdown using 2markdown","parameters":{"type": "object", "properties": {"url": {"type": "string", "description": "the url to be converted to markdown format"}}, "required": ["url"]}},
    {"name":"connect_to_database","description":"to connect to a SQL database","parameters":{"type": "object", "properties": {"user_request": {"type": "string", "description": "Summary what user want"},"database_name": {"type": "string", "description": "The database name that user provided"}}, "required": ["user_request","database_name"]}},
    {"name":"list_all_functions_and_menu","description":"to list all available functions or menus that can be asked to ChatGPT","parameters":{"type": "object", "properties": {}, "required": []}}
]


def main():
    global user_query
    # scan_folder(directory)

def main_function(ai_response):
    global messages,directory,listpath,walk_code,docs,document_db,connection
    if(ai_response["choices"][0]["message"]["function_call"]):
        function_call = ai_response["choices"][0]["message"]["function_call"]
        function_name = function_call["name"]
        arguments = function_call["arguments"]
        print("Call : "+function_name)
        # =================================== FUNCTION
        # CREATE FUNCTION SCHEMAS
        if function_name == "function_schemas_generator":
            print("Generating function schema ...")
            function_schemas=eval(arguments).get("function_schemas")
            return function_schemas
        
        # CREATE PROJECT
        elif function_name == "create_app_or_game_project":
            output=eval(arguments).get("output")
            user_input=eval(arguments).get("user_input")
            ui_properties=eval(arguments).get("ui_properties")
            core=eval(arguments).get("core")
            print(arguments)
            previous_index=len(messages)
            filepaths_string=asking_ai("You are profesional AI Mapping Debugger", os.getenv("sys_create_filepath1").replace("{question}",user_query),skipFunction=True,skipHistory=True)
            file_paths = filepaths_string[filepaths_string.index("["):filepaths_string.index("]")+1]
            shared_dependencies= asking_ai(system="you are profesional AI Mapping Dependency",user=os.getenv('sys_create_shared1').replace("{question}",user_input+" "+output+" "+ui_properties+f". {core}").replace("{filepaths_string}",file_paths),skipFunction=True,skipHistory=True)
            write_file(directory+"\\shared_dependencies.md", shared_dependencies)
            finish_stream=asking_ai_stream(system=os.getenv("sys_code_stream").replace('{question}',user_input+" "+output+" "+ui_properties+f". {core}").replace("{filepaths_string}",json.dumps(file_paths)).replace("{shared_dependancies}",shared_dependencies),
                                            user=os.getenv('sys_create_generate2').replace("{question}",user_input+" "+output+" "+ui_properties+f". {core}")
                                           )
            all_the_code="".join(finish_stream)
            extracted_code=extract_files(all_the_code)
            for code in extracted_code:
                write_file(directory+"\\"+code['filepath'].replace('\n', ''), code['filecode'] )
            messages=messages[:previous_index]
            if os.path.exists(directory):
                os.startfile(directory)  # Windows
            return "Function create_app_or_game_project finish!"
        
        # CREATE PLAIN CODE
        elif function_name == "create_plain_code":
            print("Writing the code ...")
            code=eval(arguments).get("code")
            return code

        # FIX ERROR
        elif function_name == "improve_or_fix_provided_code":
            print("fix the code")
            improve_or_fix_provided_code(False)
            return "Function improve_or_fix_provided_code finish!"

        # Scan Floder
        elif function_name == "scan_and_read_directory":
            print("Scanning ...")
            directory=eval(arguments).get("directory")
            scan_folder(directory)
            return json.dumps(listpath)
        
        # Reset Memory
        elif function_name == "reset_memory":
            resetMemory()
            return "Function reset_memory finish!"
        
        # Browsing Internet
        elif function_name == "duck_go_browser_search":
            print("Browsing ...")
            query=eval(arguments).get("query")
            query=browser.run(query)
            return query
        
        # Extract data from url
        elif function_name =="get_or_extract_scrapping_info_from_url":
            print("Get info from url ...")
            url=eval(arguments).get("url")
            content = PlaywrightURLLoader(urls=[url], remove_selectors=["header", "footer"]).load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=0)
            content=text_splitter.split_documents(content)
            document_db.extend(content) 
            response = asking_ai(user="Summary this : "+" ".join([d.page_content for d in content]),skipFunction=True)
            return response
        
        elif function_name =="extract_url_as_markdown":
            print("Extract URL to Markdown")
            url=eval(arguments).get("url")
            loader = ToMarkdownLoader(api_key="sk-e33c491c69b1e998b67e3cd6e78de833",url=url)
            docs = loader.load()
            return docs[0].page_content
        
        elif function_name == "connect_to_database":
            print("Connecting to database ...")
            database_name=eval(arguments).get("database_name")
            connection=connect_to_database(database_name)
            database_details = extract_database_details(connection)
            walk_code=walk_code+database_details
            return "Database connected"

        elif function_name == "list_all_functions_and_menu":
            return os.getenv("list_function")

        else:
            return ai_response["choices"][0]["message"]["function_call"]["arguments"]
    else:
        return ai_response["choices"][0]["message"]['content']

def asking_ai(system=False,user="",skipFunction=False,skipHistory=False):
    global messages,selection
    if system:
        messages = messages+[{"role": "system", "content": system}]
    if_there_scanned_code="" if walk_code == "" else ". Based on this : "+walk_code + "" if docs == "" else ". Or Based on this : "+docs
    messages = messages+[{"role": "user", "content": user + if_there_scanned_code}]
    if selection in ["1" ,"2" ,"4" ,"7" ,"8" ,"9" ,"10"]:
        response = openai.ChatCompletion.create(
            model=openai_model,
            messages=messages,
            temperature=temperature
        )
    else:
        response = openai.ChatCompletion.create(
            model=openai_model,
            messages=messages,
            temperature=temperature,
            functions = function_descriptions,
            function_call="none" if skipFunction else "auto"
        )
    if response["choices"][0]["finish_reason"] == "function_call":
        function_response = main_function(response)
        if(response["choices"][0]["finish_reason"] == "function_call"):
            print(response["choices"][0]["message"]["function_call"]["name"])
        if skipHistory==False:
            messages.append({
                "role": "assistant",
                "content": function_response
            })
        return function_response
    else:
        if skipHistory==False:
            messages.append({
                "role": "assistant",
                "content": response["choices"][0]["message"]["content"]
            })
        print(response["choices"][0]["message"]["content"])
        return response["choices"][0]["message"]["content"]

def asking_ai_stream(system,user):
    global messages
    chat = []
    if system:
        messages = messages+[{"role": "system", "content": system}]
    while "done" not in user:
        extra =""
        if user in ["continue","lanjut","next","go on"]:
            extra="continue and add up from the previous assistant response without any add explanation or comment, i only want you to continue it"
        messages = messages + [{"role": "user", "content": user+extra}]
        response = openai.ChatCompletion.create(
            model=openai_model,
            messages=messages,
            stream=True,
        )
        for chunk in response:
            delta = chunk['choices'][0]['delta']
            msg = delta.get('content', '')
            print(msg, end="")
            chat.append(msg)
        # messages + [{"role": "assistant", "content": "".join(chat)}] 
        user=input("The stream is finish, continue or done \nUser : " ) or "done"
    return "".join(chat)
        
# =================================================== CODE FUNCTION =====================================   

# Fungsi yang akan di eksekusi saat membuat sebuah program baru melalui stream data chatgpt
def extract_files(input_string):
    pattern = r'### (.+?)\n```[A-Za-z]+\n(.+?)\n```'
    matches = re.findall(pattern, input_string, re.DOTALL)
    result = [{'filepath': m[0], 'filecode': m[1]} for m in matches]
    return result

# Fungsi untuk menulis file ke folder
def write_file(file_path, code):
    folder_path = os.path.dirname(file_path)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    with open(file_path, 'w',encoding="utf-8") as file:
        file.write(code)

#  Fungsi yang akan di eksekusi saat menggunakan fungsi improve atau fix error code
def replace_code(parameters):
    parameters=eval(parameters)
    for param in parameters:
        filepath = param.get('filepath', '')
        filepath = filepath.replace("\\", "\\\\")
        code_to_replace = param.get('code_to_replace', '')
        replacement_code = param.get('replacement_code', '')
        new_code = param.get('new_code', '')
        filepath=filepath.replace("\\\\","/")
        filepath=filepath.replace(directory+"/","")
        # input(f"checkpoint : "+f"{directory}/new"+'/'+filepath)
        if os.path.exists(f"{directory}/new"+'/'+filepath):
            print("jalur new ")
            with open(f"{directory}/new"+'/'+filepath, 'r') as file:
                content = file.read()
                if code_to_replace=='':
                    if input("Apakah insert semua code ini ke filepath ini? y/(n)") or "n" =='y':
                        if code_to_replace:
                            print("jalur replace")
                            content=content.replace(code_to_replace,replacement_code)
                        else:
                            print("new code")
                            content=content+"\n"+new_code
                        write_file(f"{directory}/new"+'/'+filepath,content)
                else:        
                    if code_to_replace:
                        print("jalur replace")
                        content=content.replace(code_to_replace,replacement_code)
                    else:
                        print("new code")
                        content=content+"\n"+new_code
                    write_file(f"{directory}/new"+'/'+filepath,content)
        elif os.path.exists(f"{directory}/"+filepath):
            print("jalur existing")
            with open(f"{directory}/"+filepath, 'r') as file:
                content = file.read()
                if code_to_replace:
                    print("jalur replace")
                    content=content.replace(code_to_replace,replacement_code)
                else:
                    print("new code")
                    content=content+"\n"+new_code
                write_file(f"{directory}/new/"+filepath,content)
        else:
            print("jalur create ")
            write_file(filepath,replacement_code)

def improve_or_fix_provided_code(prompt=False):
    global messages,user_query,walk_code
    previous_index=len(messages)
    user_q=os.getenv("sys_improve_debug1").replace("{question}",prompt if prompt else user_query).replace("{docs}",walk_code)
    response=asking_ai(system="You are profesional AI Debugger", 
        user=user_q
        ,skipFunction=True)
    if response[0]=="{":
        response="["+response+"]"
    if type(response)==str:
        response = response[response.index("["):response.rindex("]")+1]
    replace_code(response)
    messages=messages[:previous_index]
    reportTokens(user_q)
    if os.path.exists(directory):
        os.startfile(directory)  # Windows
    if input("Memory akan di reset, apakah sudah melakukan perbaikan code ? (y)/n :  ") or "y" == "y":
        resetMemory(True)
        scan_folder(directory)

# GET ALL DATABASE FROM DOCS,CODEBASE AND PUT IT ALL INTO WALK_CODE WITH OR WITHOUT FILTERING
def filter_database(question,filter_paths=[],langchain=False):
    global walk_code
    walk_code=""
    vector_db=[]
    if filter_paths:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if os.path.join(root, file) in filter_paths:
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r',encoding="utf-8") as f:
                        content = f.read()
                        content = f'\n\nfilepath/filename : {file_path}\ncontent : '+content 
                        walk_code += content   
                        language=detect_programming_language(file_path)
                        content=TextLoader(file_path, encoding='utf-8').load()
                        if language:
                            text_splitter=RecursiveCharacterTextSplitter.from_language(language=language,chunk_size=4000, chunk_overlap=0)
                        else:
                            text_splitter=RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=0)
                        content=text_splitter.split_documents(content)
                        content[0].page_content="\nfilename or filepath : "+content[0].metadata['source']+"\n\n"+content[0].page_content
                        vector_db.extend(content) 
    if(langchain):
        if filter_paths:
            vector_db = list(filter(lambda x: x.metadata.get('source') in filter_paths, vector_db))
        vector_db=vector_db+document_db
        if(len(vector_db)>0):
            embeddings = OpenAIEmbeddings(disallowed_special=()) # menggunakan embedding punya open ai
            db = FAISS.from_documents(vector_db, embeddings)
            embedding_vector = embeddings.embed_query(question+json.dumps(filter_paths))
            docs = db.similarity_search_by_vector(embedding_vector,k=k)
            walk_code=" ".join([d.page_content for d in docs])

# Scanning folder dengan format yang tersedia
def scan_folder(directory=directory):
    global walk_code,listpath,vector_db,filter_paths
    accepted_extention=[".txt", ".html", ".xml", ".json", ".py", ".java", ".cpp", ".c", ".h", ".css", ".js", ".sql", ".php", ".rb", ".pl", ".sh",".dart"]
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(text in file for text in accepted_extention):
                file_path = os.path.join(root, file)
                if any(text in file_path for text in ignore):
                    a=0
                else:
                    listpath.append(f"{os.path.join(root, file)}")

# Fungsi yang akan di eksekusi saat menjalankan penghapusan data
def resetMemory(deleteNew=True):
    global messages,walk_code,docs,listpath,document_db
    print("Resetting Memory ...")
    messages=[];walk_code="";docs="";listpath=[];document_db=[]
    if deleteNew:
        if os.path.exists(directory+"/new"):
            shutil.rmtree(directory+"/new", ignore_errors=True)

def detect_programming_language(code):
    if ".cpp" in code:
        return Language.CPP
    elif ".go" in code:
        return Language.GO
    elif ".java" in code:
        return Language.JAVA
    elif any(extension in code for extension in [".js", ".ts"]):
        return Language.JS
    elif ".php" in code:
        return Language.PHP
    elif ".proto" in code:
        return Language.PROTO
    elif ".py" in code:
        return Language.PYTHON
    elif ".rst" in code:
        return Language.RST
    elif ".rb" in code:
        return Language.RUBY
    elif ".rs" in code:
        return Language.RUST
    elif ".scala" in code:
        return Language.SCALA
    elif ".swift" in code:
        return Language.SWIFT
    elif ".md" in code:
        return Language.MARKDOWN
    elif ".tex" in code:
        return Language.LATEX
    elif any(extension in code for extension in [".html", ".xml"]):
        return Language.HTML
    elif ".sol" in code:
        return Language.SOL
    else:
        return False

# Fungsi yang akan di eksekusi saat menjalankan connect to database
def connect_to_database(database_name):
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database=database_name
    )
    return connection

# Mendapatkan data dari database dengan query
def query_db(connection,query):
    cursor = connection.cursor()
    cursor.execute(query)
    column_names = [column[0] for column in cursor.description]
    table_data = cursor.fetchall()
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

# Mengextract semua data field dan properties nya
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

def reportTokens(prompt):
    global thetoken
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    thetoken=str(len(encoding.encode(prompt)))
    print(f"Total Token : {thetoken}")

# =================================================================================

from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return os.getenv('html').replace("{listpath}", json.dumps(listpath))

@app.route('/api/data', methods=['POST'])
def process_data():
    global db,vector_db,sistem_prompt,connection
    data = request.get_json()
    prompt=data['prompt']
    langchain=data['langchain']
    sql_generator=data['sql_generator']
    if sql_generator==False:
        filter_database(question=data['prompt'],
                        filter_paths=data['filepaths'] if data['filepaths'] else False,
                        langchain=True if langchain=="langchain" else False)
        sistem_prompt=data['sistem_prompt'] or ""
        if data['selection']=='improve':
            improve_or_fix_provided_code(prompt)
            return "improve or fix finish!"
        else:
            response = asking_ai(system=sistem_prompt,user=prompt)
            return jsonify({'message': response})
    else:
        query_generator=os.getenv("sql_generator").replace("{docs}",walk_code).replace("{prompt}",prompt)
        output=asking_ai(system=query_generator,user=prompt,skipFunction=True)
        output_query=output
        output = output[output.index("SELECT"):output.rindex(";")+1]
        result = query_db(connection,output)
        print('-----------------------result-----------------------')
        print(result['csv'])
        apex_geerator=os.getenv("ApexChart_generator").replace("{docs}",result['csv']).replace("{prompt}",prompt)
        output2=asking_ai(system=apex_geerator,user=prompt,skipFunction=True)
        obj = output2[output2.index("{"):output2.rindex("}")+1]
        print(obj)
        return jsonify({"message":{"apexchart":json.loads(output2),"query":output_query,"datanya":result['json']}})


@app.route('/api/upload', methods=['POST'])
def upload_file():
    global db,document_db
    if 'file' not in request.files:
        return 'No file provided', 400
    file = request.files['file']
    os.makedirs(directory+'/new', exist_ok=True)
    filepath=os.path.join(directory+'/new', file.filename)
    file.save(filepath)
    if(".csv" in filepath):
        content = CSVLoader(filepath).load()
    elif(".docx" in filepath):
        content = UnstructuredWordDocumentLoader(filepath, mode="elements").load()
    elif(".pdf" in filepath):
        content= PyPDFLoader(filepath).load()
    elif(".pptx" in filepath):
        content = UnstructuredPowerPointLoader(filepath).load()
    elif(".xlsx" in filepath):
        content = UnstructuredExcelLoader(filepath, mode="elements").load()
    else:
        return "Not Supported type File!"
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=0)
    content=text_splitter.split_documents(content)
    content[0].page_content="\nfilename or filepath : "+content[0].metadata['source']+"\n\n"+content[0].page_content
    document_db.extend(content) 
    return 'File uploaded successfully'

if __name__ == "__main__":
    print("1. gpt-3.5-turbo\n2. gpt-3.5-16k\n3. (gpt-3.5-16k-0613)\n4. gpt-4\n5. gpt-4-0613\n6. gpt-4-32k-0613\n7. gpt-4-poe\n8. Claude-instant-100k\n9. Claude+ \n10. Bard")
    selection = input("Pilih model : ") or selection
    if selection in ["1" ,"2" ,"3" ,"4" ,"5" ,"6" ,"10"]:
        api_url=os.getenv('catto_url')
        api_key=os.getenv('catto_key')
    else:
        api_url=os.getenv('chimera_url')
        api_key=os.getenv('chimera_key')
    if selection == "1":
        openai_model="gpt-3.5-turbo"
        k=20
    elif selection == "2":
        openai_model="gpt-3.5-turbo-16k"
        k=70
    elif selection == "3":
        openai_model="gpt-3.5-turbo-16k-0613"
        k=70
    elif selection == "4":
        openai_model="gpt-4"
        k=20
    elif selection == "5":
        openai_model="gpt-4-0613"
        k=70
    elif selection == "6":
        openai_model="gpt-4-32k-0613"
        k=150
    elif selection == "7":
        openai_model="gpt-4-poe"
        k=10
    elif selection == "8":
        openai_model="claude-instant-100k"
        k=500
    elif selection == "9":
        openai_model="claude+"
        k=50
    elif selection == "10":
        openai_model="bard"
        k=20
    else:
        selection="3"
        openai_model="gpt-4-0613"
        k=40
    directory = input("Tambahkan path scan folder/directory (default \"generated\"): ") or 'generated'
    if os.path.exists(directory+"/new"):
        shutil.rmtree(directory+"/new", ignore_errors=True)    
    main()
    def open_url():
        webbrowser.open_new_tab("http://localhost:5000")
    open_url()
    scan_folder(directory)
    port = 5000  # Replace with your desired port number
    app.run(port=port)


