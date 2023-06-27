from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.document_loaders import CSVLoader
from langchain.document_loaders import TextLoader
from langchain.document_loaders import JSONLoader
from langchain.document_loaders import PlaywrightURLLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from dotenv import find_dotenv, load_dotenv
from langchain.prompts import PromptTemplate
from langchain.docstore import InMemoryDocstore
from langchain.vectorstores import FAISS
from langchain.memory import VectorStoreRetrieverMemory
from langchain.chains import ConversationChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from pathlib import Path

import faiss
import os
import shutil
import ast
from time import sleep
import tiktoken
import requests
import json
import re

# CONFIG 
# env_path = Path('D:\\.env') #menggunakan global path .env
# load_dotenv(dotenv_path=env_path)
load_dotenv(find_dotenv()) # local .env
embeddings = OpenAIEmbeddings(disallowed_special=()) # menggunakan embedding punya open ai
index = faiss.IndexFlatL2(1536)
embedding_fn = OpenAIEmbeddings().embed_query
vectorstore = FAISS(embedding_fn, index, InMemoryDocstore({}), {})
retriever = vectorstore.as_retriever(search_kwargs=dict(k=4))
memory = VectorStoreRetrieverMemory(retriever=retriever,memory_key="chat_history")
save_memory=""
k=20 # total document yang di generate oleh vectore store
# GLOBAL Variable
api_url=os.getenv('chimera_url')
api_key=os.getenv('chimera_key')
openai_model = "gpt-4"  # 'gpt-3.5-turbo' | 'gpt-4'
openai_model_max_tokens = 4000  # untuk gpt 3.5 bisa sampai 4k , gpt 4 bisa sampai 8k - 32k
ignore=["pycache", "package","node_modules", "vendor",'wwebjs_auth','backup','.env','.md']
open_ai_temperature = 0.1  # standard pakai 0.7
database=[] # storing semua chunk ke memory databases
db=False # DB State untuk vectore store
choice=1 # gpt-3.5-turbo > bard
selection=1 # read doc, read code, create code, improve code
machine=1 # langchain=1, 2 freetext
directory="generated" # Default folder 
sistem_prompt=False # False menggunakan default prompt dari .env
urlnya=[] # list url website yang akan di extract data
listpath=[] # listfilepath yang di render di html
paths=[] # listfilepath yang akan di consume oleh langchain
pertanyaan='' #global user input dari ambilan di front end

def main(directory):
    global db,database
    walkDir(directory)
    if(machine=='1' and len(database)>0 and (choice=='1' or choice=='2' or choice=='4')): #langchain route
        print('Start FAISS ...')
        db = FAISS.from_documents(database, embeddings)

def walkDir(dir):
    global db,database,urlnya
    db=False
    database=[]
    root_dir = dir
    loadPDF()
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for file in filenames:
            try:
                check=f"{dirpath}{file}"
                if any(text in check for text in ignore):
                    print('')
                else:
                    if(choice=='2' or choice=='3' or choice=='4' or choice=='5'):
                        type_file=[".txt", ".html", ".xml", ".json", ".py", ".java", ".cpp", ".c", ".h", ".css", ".js", ".md", ".sql", ".php", ".rb", ".pl", ".sh",".dart"]
                    else: 
                        type_file=[".csv",".doc",".docx",".ppt",".pptx",".txt",'.json']
                    if any(text in file for text in type_file):
                        listpath.append(f"{dirpath}\\{file}")
                        if len(paths)>0:
                            if(f"{dirpath}\\{file}" in paths):
                                print(f"{dirpath}\\{file}")
                                processFile(dirpath,file)
                        else:
                            print(f"{dirpath}\\{file}")
                            processFile(dirpath,file)
            except Exception as e:
                pass

def processFile(dirpath,file):
    global database
    if(machine=='1'): #langchain Route
        print('jalur langchain')
        if(choice=='2' or choice=='4'): #jika membaca code
            print('Split the document '+file)
            loader = TextLoader(os.path.join(dirpath, file), encoding='utf-8')
            transcript = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=0)
            docs = text_splitter.split_documents(transcript)
            database.extend(docs)
        else: #jika membaca docs
            if(".csv" in file):
                print('Loading CSV ...')
                loader = CSVLoader(os.path.join(dirpath, file))
            elif(".json" in file):
                print('Loading JSON ...')
                loader = JSONLoader(os.path.join(dirpath, file))
            else:
                return
        transcript = loader.load()
        transcript[0].page_content=transcript[0].page_content+"\n\nfilename or filepath : "+transcript[0].metadata['source']+"\n\n"
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=0)
        docs = text_splitter.split_documents(transcript)
        database.extend(docs)   

    else: # freetext Route
        if(".csv" in file):
            print('Loading CSV ...')
            loader = CSVLoader(os.path.join(dirpath, file))
            transcript = loader.load()
            transcript=transcript[0].page_content.replace('\n', '')
        elif(".json" in file):
            print('Loading JSON ...')
            loader = JSONLoader(os.path.join(dirpath, file))
            transcript = loader.load()
            transcript=transcript[0].page_content.replace('\n', '')
        else:
            transcript = read_utf8_file(os.path.join(dirpath, file))
            transcript=transcript.replace('\n', '')
        database.append("filename or filepath: " + os.path.join(dirpath, file) + "\n\n docs : " + transcript) 

def get_response_from_question(question):
    global db,database,pertanyaan,save_memory
    response=""
    pertanyaan=question
    if(machine=='1'): #langchain Route
        if(choice=='1'): # membaca docs langchain
            if sistem_prompt:
                response=create_chat_completion(sistem_prompt, os.getenv("human_docs_1").replace("{question}",question),model=openai_model)
            else:
                response=create_chat_chain(os.getenv("sys_docs_1"),os.getenv("human_docs_1"),question,k)
        elif(choice=='2'): #membaca code langchain
            response=create_chat_chain(os.getenv("sys_code_1"),os.getenv("human_code_1"),question,k)
        elif(choice=='4'): #improve code langchain
            print("Learning the code ini ...")
            print(paths)
            response=create_chat_completion("You are profesional AI Debugger", os.getenv("sys_improve_debug1").replace("{question}",pertanyaan).replace("{docs}"," The source coming from vectore store database,\n\n "+get_similarity(question+" \n\nHere is the filepaths : "+", ".join(paths))),openai_model)
            # response=create_chat_completion("You are profesional AI Debugger", os.getenv("sys_improve_debug2").replace("{question}",pertanyaan).replace("{docs}",get_similarity(question)),openai_model)
            replace_code(response)
            print(f'Program berhasil di generate!')
        return response
    
    else: #freetext Route
        if(choice=='1'): #membaca docs
            if sistem_prompt:
                response=create_chat_completion(sistem_prompt, os.getenv("human_docs_1").replace("{question}",question),openai_model)
            else:
                response=create_chat_completion(os.getenv("sys_docs_1").replace("{docs}"," ".join(database)), os.getenv("human_docs_1").replace("{question}",question),openai_model)
        elif(choice=='2'): #membaca code
            response=create_chat_completion(os.getenv("sys_code_1").replace("{docs}"," ".join(database)), os.getenv("human_docs_1").replace("{question}",question),openai_model)
        elif(choice=='3'): #membuat code
            print("generate filepath ... "+openai_model)
            filepaths_string=create_chat_completion("You are profesional AI Mapping Debugger", os.getenv("sys_create_filepath1").replace("{question}",pertanyaan),openai_model)
            list_string = filepaths_string[filepaths_string.index("["):filepaths_string.index("]")+1]
            print(list_string)
            list_actual = ast.literal_eval(list_string)
            shared_dependencies= create_chat_completion("you are profesional AI Mapping Dependency",os.getenv('sys_create_shared1').replace("{question}",question).replace("{filepaths_string}",filepaths_string),openai_model)
            write_file("shared_dependencies.md", shared_dependencies, directory)
            print('Done generate shared Dependancies!')
            before=''
            for name in list_actual:
                print('Generating '+name)
                filename, filecode = generate_file_shared_dependancies(name,filepaths_string,shared_dependencies,question,before)
                save_memory=save_memory+f" fileath : {name}\n\n code : {filecode} \n\n"
                write_file(filename, filecode, directory)
                before=name
            print(f'Program berhasil di generate!')
            folder_path = os.getcwd()
            os.system(f'start "" "{folder_path}/{directory}/new"')
            print("Debugging the code")
            response=create_chat_completion("You are an expert code debugger, decide if you think the code is work or not the way it's , if it work then response : it works, but if it need change then response all the problem list all posible error on the base on history chat code that already generated and include all the filepath of the file that need to debug or change ", os.getenv("human_docs_1").replace("{question}","Debug and testing my code, check if there an errors or bug"),openai_model)
        elif(choice=='4'): # improve code
            print("Learning the code ini ...")
            response=create_chat_completion("You are profesional AI Debugger", os.getenv("sys_improve_debug1").replace("{question}",pertanyaan).replace("{docs}"," ".join(database)),openai_model)
            replace_code(response)
            print(f'Program berhasil di generate!')
        return response

def get_similarity(question):
    if(db):
        print(question)
        # docs = db.similarity_search(question, k=k)
        # return " ".join([d.page_content for d in docs])
        embedding_vector = embeddings.embed_query(question)
        docs = db.similarity_search_by_vector(embedding_vector,k=k)
        hasil=" ".join([d.page_content for d in docs])
        print("Total Character : "+str(len(hasil)))
        reportTokens(hasil)
        return hasil
    else:
        return ""

def saveConvertation(system,user):
    history=[f""" User:{user}\n AI:{system} \n"""]
    vectorstore.add_texts(texts=history)

def get_history(question,c=k):
    docs = vectorstore.similarity_search(question, k=c)
    return " ".join([d.page_content for d in docs])

def saveDocument(docs):
    global db
    db.add_documents(docs)

def create_chat_chain(system, user, question,k):
    global db,database
    print('using chain')
    # system=system.replace("{docs}",get_similarity(question))+" \n\nChat History = \n"+get_history(pertanyaan)
    system=system+" \n\nChat History = \n"+get_history(pertanyaan)
    user=user.replace("{question}",pertanyaan)
    chat = ChatOpenAI(model_name=openai_model, temperature=open_ai_temperature)
    chat_prompt = ChatPromptTemplate.from_messages(
        [SystemMessagePromptTemplate.from_template(system), HumanMessagePromptTemplate.from_template(user)]
    )
    chain = LLMChain(llm=chat, prompt=chat_prompt)
    print('generate response ...')
    response = chain.run(docs=get_similarity(question))
    saveConvertation(response,pertanyaan)
    return response

def create_convertation_chain(system, user, question):
    global db,database
    print('using chain')
    system=system.replace("{docs}",get_similarity(question))
    user=user.replace("{question}",pertanyaan)
    chat = ChatOpenAI(model_name=openai_model, temperature=open_ai_temperature)
    _DEFAULT_TEMPLATE = system+"""
    Relevant pieces of previous conversation:
    {chat_history}
    (You do not need to use these pieces of information if not relevant)
    Current conversation:
    Human: {input}
    AI:"""
    PROMPT = PromptTemplate(
        input_variables=["chat_history", "input"], template=_DEFAULT_TEMPLATE
    )
    conversation_with_summary = ConversationChain(
        llm=chat, 
        prompt=PROMPT,
        memory=memory,
        verbose=True
    )
    response=conversation_with_summary.predict(input=user)
    saveConvertation(response,pertanyaan)
    return response


def create_chat_completion(system,user,model,history=False):
    if history:
        system=system+" \n\nChat History = \n"+get_history(history,k)
    else:
        system=system+" \n\nChat History = \n"+get_history(pertanyaan)
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer '+api_key
    }
    # print("---------------- sistem ---------------------")
    # print(system)
    # print("---------------- sistem ---------------------")
    params = {
        "model": model, #"claude-instant-100k"
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        # "max_tokens": openai_model_max_tokens,
        "temperature": open_ai_temperature, 
    }
    # print(params)
    response=""
    try:
        response = requests.post(api_url, json=params, headers=headers)
    except:
        print(params)
    result = response.json()
    hasil= result['choices'][0]['message']['content']
    saveConvertation(hasil,pertanyaan)
    return hasil

def generate_file_shared_dependancies(
    filename, filepaths_string=None, shared_dependencies=None, prompt=None, before=''
):
    global pertanyaan
    start_marker = f"### {filename}"
    end_marker = "###"
    start_index = shared_dependencies.find(start_marker)
    if start_index != -1:
        end_index = shared_dependencies.find(end_marker, start_index + len(start_marker))
        if end_index != -1:
            content = shared_dependencies[start_index + len(start_marker):end_index].strip()
            prompt=prompt+f" as for now we focusing to generate code for file {filename}, and here a snippet of structure that you need to build : {content}"
            pertanyaan=prompt
            print(pertanyaan)
            filecode = create_chat_completion(os.getenv('sys_create_generate1').replace('{question}',prompt).replace("{filename}",filename).replace("{filepaths_string}",filepaths_string).replace("{shared_dependancies}",shared_dependencies),
                                      os.getenv('sys_create_generate2').replace("{question}",prompt).replace("{filename}",filename),
                                      openai_model,content
                                      )
            return filename, filecode
def generate_file_improve(
    filename, filepaths_string=None, question=None, type="langchain",source=""
):
    if(type == "langchain"):
        filecode = create_chat_completion(os.getenv('sys_improve_generate1').replace("{question}",question).replace("{filepaths_string}",filepaths_string).replace("{docs}",get_similarity(question+f" {filename}")),
                                      os.getenv('sys_create_generate1b').replace("{question}",question).replace("{filename}",filename),
                                      openai_model
                                      )
    else:
        filecode = create_chat_completion("You are a Profesional Code Generation AI who can improve or fix code between file",
                                      os.getenv('sys_improve_generate1').replace("{question}",question).replace("{filename}",filename).replace("{docs}",source),
                                      openai_model
                                      )
    return filename, filecode

from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return os.getenv('html').replace("{listpath}", json.dumps(listpath))

@app.route('/api/data', methods=['POST'])
def process_data():
    global db,database,sistem_prompt,paths
    data = request.get_json()
    prompt=data['prompt']
    paths=data['filepaths']
    walkDir(directory)
    saveConvertation("","")
    if(machine=='1' and len(database)>0 and (choice=='1' or choice=='2' or choice=='4')): #langchain route
        print('Start FAISS ...')
        db = FAISS.from_documents(database, embeddings)
    sys_prompt=data['sistem_prompt'] if len(data['sistem_prompt'])>0 else False
    sistem_prompt=sys_prompt
    response = get_response_from_question(prompt)
    response_data = {'message': response}
    return jsonify(response_data)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    global db,database,embeddings
    if 'file' not in request.files:
        return 'No file provided', 400

    file = request.files['file']
    os.makedirs(directory+'/new', exist_ok=True)
    file.save(os.path.join(directory+'/new', file.filename))
    walkDir(directory)
    if(machine=='1'): #langchain route
        db = FAISS.from_documents(database, embeddings)
    return 'File uploaded successfully'

@app.route('/api/add-web', methods=['POST'])
def add_web():
    global urlnya,db
    data = request.get_json()
    if len(data['urlnya'])>0:
        loader = PlaywrightURLLoader(urls=[data['urlnya']], remove_selectors=["header", "footer"])
        transcript = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=4000, chunk_overlap=0)
        docs = text_splitter.split_documents(transcript)
        saveDocument(docs)
    return 'File uploaded successfully'


def loadPDF():
    global database
    if(choice=='1'):
            loader = PyPDFDirectoryLoader(os.path.join(directory))
            transcript = loader.load()
            if(machine=='1'):
                if(len(transcript)>0): #Load PDF
                    print("Load PDF Directory ...")
                text_splitter = CharacterTextSplitter(chunk_size=4000, chunk_overlap=0)
                docs = text_splitter.split_documents(transcript)
                database.extend(docs)
            else:
                for doc in transcript:
                    database.append(doc.page_content)
                    
def read_utf8_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        return content
    
def reportTokens(prompt):
    print('--------------------------')
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    print(str(len(encoding.encode(prompt)))
        + " tokens di prompt : "
        + prompt[:50]
    )

def replace_code(parameters):
    json_str = parameters[parameters.index("["):].replace("\n", "")
    output=ast.literal_eval(json_str)
    i=0
    if type(output)==dict:
        output=output['fixes']
    for param in output:
        filepath = param['filepath']
        filepath = filepath.replace("\\", "\\\\")
        code_to_replace = param['code_to_replace']
        replacement_code = param['replacement_code']
        i=i+1
        print("-------------------------------------")
        print(filepath)
        print(code_to_replace)
        print(replacement_code)
        tanya=input("Gunakan code ini ? (y)/n  ") or 'y'
        if(tanya == 'y'):
            if os.path.exists(f"{directory}\\\\new"+'\\\\'+filepath):
                with open(f"{directory}\\\\new"+'\\\\'+filepath, 'r') as file:
                    content = file.read()
                    content=content.replace(code_to_replace,replacement_code)
                    write_file(filepath,content,directory)
            elif os.path.exists(filepath):
                with open(filepath, 'r') as file:
                    content = file.read()
                    content=content.replace(code_to_replace,replacement_code)
                    write_file(filepath,content,directory)
            else:
                write_file(filepath,replacement_code,directory)
                print(f"Create new file {filepath}")

def extract_json_data(json_string):
    start_index = json_string.find("[")
    end_index = json_string.rfind("]")
    if start_index != -1 and end_index != -1:
        json_data = json_string[start_index:end_index+1]
        try:
            data = json.loads(json_data)
            return data
        except json.JSONDecodeError:
            print("Invalid JSON data.")
            return None
    else:
        print("JSON data not found.")
        return None

def write_file(filename, filecode, directory):
    file_path = directory + "/new/" + filename
    dir = os.path.dirname(file_path)
    os.makedirs(dir, exist_ok=True)
    if os.path.exists(file_path):
        shutil.rmtree(file_path, ignore_errors=True)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(filecode)

def write_file_origin(filepath, filecode):
    file_path = filepath
    dir = os.path.dirname(file_path)
    os.makedirs(dir, exist_ok=True)
    if os.path.exists(file_path):
        shutil.rmtree(file_path, ignore_errors=True)
    with open(file_path, "w", encoding="utf-8") as file:
        file.write(filecode)

if __name__ == "__main__":
    print("""
    1. gpt-3.5-turbo
    2. gpt-3.5-16k
    3. gpt-3.5-16k-0613
    4. gpt-4
    5. gpt-4-0613
    6. gpt-4-32k-0613
    7. gpt-4-poe
    8. Claude-instant-100k
    9. Claude+ 
    10. Bard
    """)
    default_selection="1"
    default_choice="2"
    default_machine="2"
    selection = input("Pilih model : ") or default_selection
    if selection == "1":
        openai_model="gpt-3.5-turbo"
        api_url=os.getenv('catto_url')
        api_key=os.getenv('catto_key')
        openai_model_max_tokens=4000
        k=20
    elif selection == "2":
        openai_model="gpt-3.5-turbo-16k"
        api_url=os.getenv('catto_url')
        api_key=os.getenv('catto_key')
        openai_model_max_tokens=15000
        k=70
    elif selection == "3":
        openai_model="gpt-3.5-turbo-16k-0613"
        api_url=os.getenv('catto_url')
        api_key=os.getenv('catto_key')
        openai_model_max_tokens=15000
        k=70
    elif selection == "4":
        openai_model="gpt-4"
        api_url=os.getenv('catto_url')
        api_key=os.getenv('catto_key')
        openai_model_max_tokens=4000
        k=20
    elif selection == "5":
        openai_model="gpt-4-0613"
        api_url=os.getenv('catto_url')
        api_key=os.getenv('catto_key')
        openai_model_max_tokens=15000
        k=70
    elif selection == "6":
        openai_model="gpt-4-32k-0613"
        api_url=os.getenv('catto_url')
        api_key=os.getenv('catto_key')
        openai_model_max_tokens=30000
        k=150
    elif selection == "7":
        openai_model="gpt-4-poe"
        api_url=os.getenv('chimera_url')
        api_key=os.getenv('chimera_key')
        openai_model_max_tokens=2000
        k=10
    elif selection == "8":
        openai_model="claude-instant-100k"
        api_url=os.getenv('chimera_url')
        api_key=os.getenv('chimera_key')
        openai_model_max_tokens=100000
        k=500
    elif selection == "9":
        openai_model="claude+"
        api_url=os.getenv('chimera_url')
        api_key=os.getenv('chimera_key')
        openai_model_max_tokens=10000
        k=50
    elif selection == "10":
        openai_model="bard"
        api_url=os.getenv('catto_url')
        api_key=os.getenv('catto_key')
        openai_model_max_tokens=4000
        k=20
    else:
        selection="3"
        openai_model="gpt-4-0613"
        api_url=os.getenv('chimera_url')
        api_key=os.getenv('chimera_key')
        openai_model_max_tokens=8000
        k=40
    print("""
    1. Read doc, supported Document (pdf,csv,json,txt)
    2. Read debug code
    3. Create code
    4. Improve code
    """)
    choice = input("Pilih Aksi : ") or default_choice
    if(choice==""):
       choice="1"
    if(choice=='1' or choice =='2' or choice=='3' or choice =='4'):
        warning = " Pastikan PDF Bukan gambar\n\n" if choice =="1" else " code\n\n"
        error = "  Tidak support untuk create code " if choice=='3' else ''
        print("\n1. Langchain"+error+"\n2. Freetext"+warning)
        machine = input("Pilih opsi : ") or default_machine
    directory = input("Tambahkan path scan folder : ") or 'generated'
    if os.path.exists(directory+"/new"):
        shutil.rmtree(directory+"/new", ignore_errors=True)
    print(f"selection : {selection}, choice {choice}, machine {machine}, directory {directory}")
    main(directory)
    saveConvertation("","")
    # webbrowser.open("http://localhost:5000")
    port = 5000  # Replace with your desired port number
    app.run(port=port)

    