#!/usr/bin/env python3

import openai
import json
import os
import traceback
import sys
import shutil
import webbrowser
import re
import time
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader


from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv()) # local .env

import all_functions
from flask import Flask, request, jsonify
app = Flask(__name__)


openai.api_base=os.getenv("openai_base")
openai.api_key = os.getenv("openai_key")
openai_model="gpt-3.5-turbo-16k-0613"
# GLOBAL VARIABLE
listpath=[]
directory="code"
directory=input(f"Default folder : ({directory})  ") or directory
print(f"Directory : {directory}")
print("1. gpt-3.5-turbo-16k-0613\n2. gpt-3.5-turbo-0613\n3. gpt-4-0613\n4. gpt-4-32k-0613")
temperature=0.31
selection=input(f"Pilih gpt model : ({openai_model})  ") or openai_model
if selection=="1":
    openai_model="gpt-3.5-turbo-16k-0613"
    temperature=0.31
elif selection=="2":
    openai_model="gpt-3.5-turbo-0613"
    temperature=0.31
elif selection=="3":
    openai_model="gpt-4-0613"
    temperature=0.91
elif selection=="4":
    openai_model="gpt-4-32k-0613"
    temperature=0.91
else:
    openai_model="gpt-3.5-turbo-16k-0613"
    temperature=0.31
port=5000
port=int(input(f"Pilih Port ({port}) : ") or port)
prompt=""
messages = []
document_db=[]
walk_code=""
k=20
retry=0
improve=False
chain_selection=False
system_main_prompt="""
You are a Super AI bot that can do anything by writing and reading files form the computer. You have been given specific functions that you can run. Only use those functions, and do not respond with a message directly. The user will describe their project to you and you will help them build it. 
Build the project step by step by calling the provided functions you do not need to explain each step, no theory just do action the best as you can. If you need any clarification, use the ask_clarification function. You are currently inside the base folder of the project. All commands will be run from there. Use relative paths.

As an AI text-based assistant, you can provide the full source code of a file when asked .
Always make sure all the code have no error undefined, unmatch or null.

It is vital to keep the directory structure of the project simple and not to create unnecessary directories.
When you are finish with all the step make sure to run project_finished Function.
No Content on the response when trying to function_call
"""
# system_main_prompt="You are an AI bot that can do anything by writing and reading files form the computer. You have been given specific functions that you can run. Only use those functions, and do not respond with a message directly. The user will describe their project to you and you will help them build it. Build the project step by step by calling the provided functions you only need to add step explanation on the first step after that 'no theory more action', on each step make sure all the variable and function proper connection between it. If you need any clarification, use the ask_clarification function. Answer the best as you can, if you need more information from the internet then use browser_search function. You are currently inside the base folder of the project. All commands will be run from there. Use relative paths. As an AI text-based assistant, you can provide the full source code of a file when asked. It is vital to keep the directory structure of the project simple and not to create unnecessary directories. When you are finish with all the step then run project_finished Function"

def main():
    global listpath,port
    # WARN IF THERE IS CODE ALREADY IN THE PROJECT
    list_path=json.dumps(all_functions.list_files("", False,default_dir=directory))
    if os.path.exists(f"{directory}") and len(os.listdir(directory)) != 0:
        answer = yesno(f"WARNING! There is already some code in the `{directory}` folder. GPT-AutoPilot may base the project on these files and has write access to them and might modify or delete them.\n\n" + list_path + "\n\nDo you want to continue?", ["YES", "NO", "DELETE"])
        if answer == "DELETE":
            shutil.rmtree(f"{directory}")
        elif answer != "YES":
            sys.exit(0)
        elif answer == "YES":
            scan_folder(directory)
            print(list_path)

    # CREATE CODE DIRECTORY
    if not os.path.exists(f"{directory}"):
        os.mkdir(directory)
    listpath=all_functions.list_files("", False,default_dir=directory)
    webbrowser.open_new_tab(f"http://localhost:{port}")
    app.run(port=port)



def actually_write_file(filename, content):
    filename = safepath(filename,directory)
    if directory not in filename:
        if len(os.path.join(directory, filename))>=len(directory)+len(filename):
            filename = os.path.join(directory, filename)
        else:
            filename = directory+ filename
    print(f"FUNGSI: Writing to file {filename}...")

    parts = re.split("```.*?\n", content + "\n")
    if len(parts) > 2:
        content = parts[1]

    # force newline in the end
    if content[-1] != "\n":
        content = content + "\n"

    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(f"{filename}")
    os.makedirs(parent_dir, exist_ok=True)

    with open(f"{filename}", "w",encoding="utf-8") as f:
        f.write(content)

def actually_write_documentation(filename, content):
    filename = safepath(filename,directory)
    if directory not in filename:
        if len(os.path.join(directory, filename))>=len(directory)+len(filename):
            filename = os.path.join(directory, filename)
        else:
            filename = directory+ filename
    print(f"FUNGSI: Writing Documentation to file {filename}...")
    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(f"{filename}")
    os.makedirs(parent_dir, exist_ok=True)

    with open(f"{filename}", "w",encoding="utf-8") as f:
        f.write(content)

def safepath(path,default_dir):
    base = os.path.abspath(default_dir)
    if len(os.path.join(base, path))>=len(base)+len(path):
        file = os.path.abspath(os.path.join(base, path))
    else:
        file = os.path.abspath(base+ path)
    print(file)
    if os.path.commonpath([base, file]) != base:
        print("ERROR: Tried to access file outside of code/ folder!")
        sys.exit(1)

    return path

# MAIN FUNCTION
def run_conversation(prompt):
    global messages,walk_code,improve,directory,chain_selection
    improve=True
    print("Run main function")
    if messages == []:

        # SYSTEM MAIN PROMPT
        messages.append({
            "role": "system",
            "content": system_main_prompt
        })

        l_file=all_functions.list_files(default_dir=directory)
        if len(l_file)>0:
            prompt += "\n\n" + f"List of files in the project:\n{json.dumps(l_file)}"
   

    if_there_scanned_code="" if walk_code == "" else ". Based on this : "+walk_code 
    # add user prompt to chatgpt messages
    messages = send_message({"role": "user", "content": prompt+if_there_scanned_code}, messages)

    # get chatgpt response
    message = messages[-1]

    mode = None
    filename = None
    function_call = "auto"
    print_message = True
    notFinish=True

    # loop until project is finished
    while notFinish:
        if message.get("function_call"):
            # get function name and arguments
            function_name = message["function_call"]["name"]
            arguments_plain = message["function_call"]["arguments"]
            arguments = None

            try:
                arguments = json.loads(arguments_plain)
            except:
                try:
                    print("ERROR:    Invalid JSON arguments. Fixing...")
                    arguments_fixed = arguments_plain.replace("`", '"')
                    arguments = json.loads(arguments_fixed)
                except:
                    try:
                        print("ERROR:    Invalid JSON arguments. Fixing again...")
                        arguments_fixed = re.sub(r'(\b\w+\b)(?=\s*:)', r'"\1"')
                        arguments = json.loads(arguments_fixed)
                    except:
                        try:
                            print("ERROR:    Invalid JSON arguments. Fixing third time...")
                            arguments_fixed = re.sub(r"'(\b\w+\b)'(?=\s*:)", r'"\1"')
                            arguments = json.loads(arguments_fixed)
                        except:
                            print("ERROR:    Failed to parse function arguments")
                            if function_name == "replace_text":
                                function_response = "ERROR! Please try to replace a shorter text or try another method"
                            else:
                                function_response = "Error parsing arguments. Make sure to use properly formatted JSON, with double quotes. If this error persist, change tactics"

            arguments["default_dir"]=directory
            arguments["improve"]=improve
            if arguments is not None:
                # call the function given by chatgpt
                if("functions." in function_name):
                    function_name=function_name.split(".")[1]
                if hasattr(all_functions, function_name):
                    function_response = getattr(all_functions, function_name)(**arguments)
                    
                else:
                    print(f"NOTICE: GPT called function '{function_name}' that doesn't exist.")
                    function_response = f"Function '{function_name}' does not exist."

            if function_name == "write_file":
                mode = "WRITE_FILE"
                filename = arguments["filename"]
                function_call = "none"
                print_message = False

            if function_name == "write_documentation":
                mode = "WRITE_DOCUMENTATION"
                filename = arguments["filename"]
                function_call = "none"
                print_message = False

            if function_name == "ask_clarification":
                return {"status":False,"message":function_response}
            
            if function_name == "reset_memory":
                print("Reset Memory Success!")
                notFinish=False
                print_message = False
                messages=[]
                messages.append({
                    "role": "system",
                    "content": system_main_prompt
                })
                walk_code=""
                l_files=all_functions.list_files("", False,default_dir=directory)
                filter_database(prompt,l_files,chain_selection)
                return {"status":True,"message":messages}
            
            if function_name == "list_files":
                print("============ LISTING FILE ===============")
                print_message = False
                function_response=json.dumps(function_response)

            messages = remove_hallucinations(messages)
            # if function returns PROJECT_FINISHED, exit
            if function_response == "PROJECT_FINISHED":
                print("## Project finished! ##")
                notFinish=False
                if os.path.exists(directory):
                    os.startfile(directory)  # Windows
                # messages=messages[:1]
                # l_files=all_functions.list_files("", False,default_dir=directory)
                # filter_database(prompt,l_files,chain_selection)
                # walk_code=""
                return {"status":True,"message":messages}
           

            # send function result to chatgpt
            messages = send_message({
                "role": "function",
                "name": function_name,
                "content": function_response,
            }, messages, function_call, 0, print_message,mode)
        else:
            if mode == "WRITE_FILE":
                actually_write_file(filename, message["content"])
                user_message = f"File {filename} written successfully"

                mode = None
                filename = None
                function_call = "auto"
                print_message = True
            elif mode == "WRITE_DOCUMENTATION":
                actually_write_documentation(filename, message["content"])
                user_message = f"Documentation {filename} written successfully"

                mode = None
                filename = None
                function_call = "auto"
                print_message = True
            else:
                if len(message["content"]) > 400:
                    user_message = ""
                # if chatgpt doesn't respond with a function call, ask user for input
                if "?" in message["content"] or \
                   "Let me know" in message["content"] or \
                   "Please provide" in message["content"] or \
                   "Could you" in message["content"] or \
                   "Can you" in message["content"] or \
                   "Do you know" in message["content"] or \
                   "Tell me" in message["content"] or \
                   "Explain" in message["content"] or \
                   "What is" in message["content"] or \
                   "How does" in message["content"]:
                    user_message = input("You:\n")
                    print()
                else:
                    # if chatgpt doesn't ask a question, continue
                    user_message = "Ok, continue."

            # send user message to chatgpt
            messages = send_message({
                "role": "user",
                "content": user_message,
            }, messages)

        # save last response for the while loop
        message = messages[-1]
    improve=True
    # Removing All function role
    # messages = [
    #     obj for obj in messages if (
    #         obj.get("role") != "function" and 
    #         obj.get("role") != "assistant" or 
    #         "function_call" not in obj or 
    #         obj.get("function_call", {}).get("name") is not None
    #     )
    # ]

    return {"status":True,"message":messages}

def yesno(prompt, answers = ["y", "n"]):
    answer = ""
    while answer not in answers:
        slash_list = '/'.join(answers)
        answer = input(f"{prompt} ({slash_list}): ")
        if answer not in answers:
            or_list = "' or '".join(answers)
            print(f"Please type '{or_list}'")
    return answer

def remove_hallucinations(messages):
    for msg in messages:
        if msg["role"] == "function" and msg["name"] == "write_file":
            try:
                args = json.loads(msg["function_call"]["arguments"])
                if "content" in args:
                    args.pop("content")
                    msg["function_call"]["arguments"] = json.dumps(args)
            except:
                continue
    return messages

def scan_folder(directory=directory):
    global walk_code,listpath,vector_db,filter_paths
    accepted_extention=[".txt", ".html", ".xml", ".json", ".py", ".java", ".cpp", ".c", ".h", ".css", ".js", ".sql", ".php", ".rb", ".pl", ".sh",".dart"]
    for root, dirs, files in os.walk(directory):
        for file in files:
            if any(text in file for text in accepted_extention):
                file_path = os.path.join(root, file)
                if any(text in file_path for text in ["pycache", "package","node_modules", "vendor",'wwebjs_auth','backup','.env','.md']):
                    a=0
                else:
                    listpath.append(f"{os.path.join(root, file)}")

def filter_database(question,filter_paths=[],langchain=False):
    global walk_code,chain_selection
    filter_paths=list(map(lambda x: directory+x, filter_paths)) # sama dengan [1,2,3,4].map(e=>e*2) 
    walk_code=""
    vector_db=[]
    if filter_paths:
        for root, dirs, files in os.walk(directory):
            for file in files:
                if os.path.join(root, file) in filter_paths:
                    file_path = os.path.join(root, file)
                    print(file_path.replace(directory,""))
                    with open(file_path, 'r',encoding="utf-8") as f:
                        content = f.read()
                        actual_path=file_path.replace(directory,"")
                        content = f'\n\nfilepath/filename : {actual_path}\ncontent : '+content 
                        walk_code += content
                        language=detect_programming_language(file_path)
                        print(language)
                        if chain_selection:
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

def send_message(
    message,
    messages,
    function_call = "auto",
    retries = 0,
    print_message = True,
    mode=None,
    model=openai_model
):
    global retry,temperature
    messages.append(message)

    print(f"{model} Thingking ...")
    try:
        # send prompt to chatgpt
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            functions=all_functions.definitions,
            function_call=function_call,
            temperature=temperature

        )
    except openai.error.AuthenticationError:
        print("AuthenticationError: Check your API-key")
        sys.exit(1)
    except openai.error.PermissionError:
        raise
    except Exception as e:
        print("Error:", e)
        print("Retrying in 5 seconds...")
        retry=retry+1
        if retry >= 5:
            raise
        # if request fails, wait 5 seconds and try again
        print("ERROR in OpenAI request... Trying again")
        time.sleep(5+retry)
        previous_index=len(messages)-retry
        messages=messages[:previous_index]
        return send_message(message, messages, function_call, retries + 1)

    # add response to message list
    messages.append(response["choices"][0]["message"])

    # get message content
    response_message = response["choices"][0]["message"]["content"]

    # if response includes content, print it out
    if print_message and response_message != None:
        print("## ChatGPT Responded ##\n```\n")
        print(response_message)
        print("\n```\n")

    return messages


def make_better(prompt):
    if len(prompt.split(" ")) < 80:
        words = "an 80 word"
    else:
        words = "a more"

    messages = [ {     "role": "system",     "content": "You are a prompt designer for an AI agent that can read and write files from the filesystem and run commands on the computer. The AI agent is used to create all kinds of projects, including programming and content creaton. Please note that the agent can not run GUI applications or run tests. Only describe the project, not how it should be implemented. The prompt will be given to the AI agent as a description of the project to accomplish." }, 
                {     "role": "user",     "content": "Convert this prompt into "+ words +" detailed prompt:\n" + prompt }
    ]
    # print("---------------------------MESSAGE---------------------------")
    # print(messages)
    response = openai.ChatCompletion.create(
        model=openai_model,
        messages=messages,
        temperature=1.0
    )
    resp=response["choices"][0]["message"]["content"]
    print(f"Better Prompt : {resp}")
    return resp

@app.route('/', methods=['GET'])
def home():
    return html.replace("{listpath}", json.dumps(listpath))

@app.route('/api/data', methods=['POST'])
def process_data():
    global prompt,walk_code,improve,chain_selection
    data = request.get_json()
    prompt=data['prompt']
    chain_selection=data['langchain']
    if len(data['filepaths'])>0:
        filter_database(question=data['prompt'],
                filter_paths=data['filepaths'] if data['filepaths'] else False,
                langchain=True if chain_selection=="langchain" else False)
    print("==========improve===========")
    print(improve)
    if len(walk_code)>0:
        improve=True
        print("SKIP PROMPT BETTER")
    else:
        if(improve):
            improve=True
            print("SKIP PROMPT BETTER")
        else:
            # if input("Make the prompt better ? (y)/n :  ") or "y":
            better_prompt = make_better(prompt)
            prompt = better_prompt
    # RUN CONVERSATION
    response=run_conversation(prompt)
    return jsonify({"message":response})


html='''
<!DOCTYPE html>
<html>
<head>
    <title>Flask App</title>
    <link rel="stylesheet" href="https://web-raker-deploy.vercel.app/all.css">
    <script src="https://unpkg.com/vue@3/dist/vue.global.js"></script>
    <style>
     #messages {
        flex-grow: 1;
        overflow-y: auto;
        padding: 0 10px;
    }
    #gfg {
        overflow-x: auto;
        white-space: pre-wrap;
        word-wrap: break-word;
        font-size: 15px;
    }
    pre {
        overflow-x: auto;
    }
    </style>
</head>
<body>
    <div id="app">
        <div class="row justify-content-center pb-5">
            <div class="col-10">
                <div class="shadow rounded-sm p-3">
                    <h1>Hello. M.A.L.I.K.I here, what i can help you today ?</h1>
                    <hr>
                    <div class="row">
                        <div class="col-6">
                        </div>
                        <div class="col-6">
                            <select class="form-control" @change="saveSelection" v-model="vdata.langchain">
                                <option value="langchain">Vector DB</option>
                                <option value="freetext">Plain Text</option>
                            </select>
                        </div>
                    </div>
                    <hr>
                    <div class="row">
                        <div class="col-6">
                           <button type="button" @click="pilih(1)" class="btn btn-sm btn-dark  ">Documentasion Gen</button>
                           <button type="button" @click="pilih(2)" class="btn btn-sm btn-dark ml-3">Tech Documentasion Gen</button>
                           <form action="" @submit.prevent="submit">
                              <p class="text-xs">User Prompt : </p>
                              <div class="sm-form">
                                  <textarea type="text" id="prompt" name="prompt"  placeholder="prompt..." cols="6" rows="6"  class="form-control md-textarea" v-model="vdata.prompt" ></textarea>
                              </div>
                              <hr>
                              <button type="submit" class="btn btn-sm btn-dark  ">Ask AI</button>
                          </form>
                        </div>
                        <div class="col-6">
                         <div class="mt-2 shadow rounded-lg p-3" id="messages" >
                            <button type="button" @click="toggleSelect" class="btn btn-sm btn-dark  ">Select ALL</button>
                            <ul >
                                <li v-for="(item,index) in listpath" :keys="index+`key`" >
                                    <label :for="item">{{item}}</label>
                                    <input type="checkbox" :id="item" :value="item" v-model="vdata.filepaths" />
                                </li>
                            </ul>
                            <hr/>
                        </div>
                        </div>
                    </div>
                    <hr>
                    <div class="sm-form">
                        <pre id="gfg" v-text="response"></pre>
                    </div>
                </div>
            </div>
        </div>
    </div>
    <script>
      const { createApp } = Vue
      createApp({
        data() {
          return {
            vdata:{
                sistem_prompt:false,
                filepaths:{listpath},
                langchain:"freetext",
                selection:"free",
            },
            listpath:{listpath},
            path:false,
            response: false
          }
        },
        methods:{
            saveSelection(){
              localStorage.setItem("selection",this.vdata.selection)
              localStorage.setItem("langchain",this.vdata.langchain)
              localStorage.setItem("prompt",this.vdata.prompt)
            },
            toggleSelect(){
                if(this.vdata.filepaths.length>0){
                    this.vdata.filepaths=[]
                }else{
                    this.vdata.filepaths=this.listpath
                }
            },
            pilih(q){
                if(q=="1"){
                    this.vdata.prompt=`Write me a good documentation about the app that include section : Project Name, Introduction, Installation(if need it), Usage (how to use the code), Configuration (if need it), Features, API Documentation (if included), FAQ, Troubleshooting, License(MIT). Make sure to write all the text for the documentation and include info about how to contact me github(AkbarMaliki) phone(+6282251970006) email(taufikakbarmalikitkj@gmail.com)`
                }else if(q=="2"){
                    this.vdata.prompt=`Write me a good technical documentation on each code of the code in the app, make sure to seperate the document base on the file and write it on markdown style and with (.md) format. On each generation documentaion include section : Project Name, Introduction, Code Explanation (Explain only on important part of the code for main functionality and explain the code work. You do not need to explain the styling code {*.css,*.style}), Configuration (if need it), License(MIT). Make sure to write all the text for the documentation and include info about how to contact me github(AkbarMaliki) phone(+6282251970006) email(taufikakbarmalikitkj@gmail.com).`
                }
            },
            upload(e){
                let that=this
                that.response="Uploading data ..."
                let file=e.target.files[0]
                let fd = new FormData()
                fd.append("file",file)
                fetch("/api/upload",{
                    method:"POST",
                    body:fd
                }).then(response=> response.text()).then(res=>{
                    let txt=document.getElementById("response")
                    that.response=res
                    this.$forceUpdate()
                })
            },
            submit(){
                this.response="loading ..."
                let that=this;
                this.vdata.next_question=false
                this.saveSelection()
                fetch("/api/data", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(this.vdata)
                })
                .then(function(response) {
                    return response.json();
                })
                .then(function(data) {
                    // document.getElementById("pretext").innerHTML=data.message
                    that.response=data.message
                    if(!data.message["status"]){
                        that.response=data.message["message"]
                    }else{
                        that.response=data.message["message"]
                    }
                    that.$forceUpdate();
                    console.log(data.message);
                })
            },
            isJSON(str) {
                try {
                    JSON.parse(str);
                } catch (e) {
                    return false;
                }
                return true;
            }
        },
        mounted(){
            if(this.vdata.filepaths.length>0){
                this.response="Get Code from directory"
            }
            if(localStorage.getItem("selection")){
                this.vdata.selection=localStorage.getItem("selection")
            }
            if(localStorage.getItem("langchain")){
                this.vdata.langchain=localStorage.getItem("langchain")
            }
            if(localStorage.getItem("prompt")){
                this.vdata.prompt=localStorage.getItem("prompt")
            }
        }
      }).mount("#app")
    </script>
</body>
</html>
'''

main()