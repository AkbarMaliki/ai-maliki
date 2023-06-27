import os
import shutil
import subprocess
import sys
import requests
import json
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv()) # local .env

# Implementation of the functions given to ChatGPT
def replace_file(filename, replace, content,default_dir,improve):
    filename = safepath(filename,default_dir,improve)
    print(f"FUNGSI: Replace to file {filename}...")
    if default_dir not in filename:
        if len(os.path.join(default_dir, filename))>=len(default_dir)+len(filename):
            filename = os.path.join(default_dir, filename)
        else:
            filename = default_dir + filename
    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(f"{filename}")
    os.makedirs(parent_dir, exist_ok=True)
    print("============ REPLACE ================")
    print(replace)
    print("============ WITH THIS CONTENT ================")
    print(content)
    print("==============PATH==================")
    print(filename)
    # if input("ARE YOU SURE TO REPLACE THAT CONTENT ? y/(n)") or "n" =="y":
    with open(f"{filename}", 'r') as file:
        file_content = file.read()
        file_content=file_content.replace(replace,content)
        with open(f"{filename}", 'w',encoding="utf-8") as file:
            file.write(file_content)
    # with open(f"{filename}", "a") as f:
    #     f.write(file_content)
    return f"File {filename} replace successfully"
    # else:
    #     return f"File {filename} Skip to Replace"

def write_file(filename,default_dir,improve):
    return f"Please respond in your next response with the full content of the file {filename}. Respond only with the contents of the file, no explanations. Create a fully working, complete file with no limitations on file size. "

def write_documentation(filename,default_dir,improve):
    return f"Please respond in your next response with the full content of the file {filename} documentation with (.md) format. complete file with no limitations on file size."

def reset_memory(question,default_dir,improve):
    return "Reset Memory Success!"

def append_file(filename, content,default_dir,improve):
    filename = safepath(filename,default_dir,improve)
    print(f"FUNGSI: Appending to file {filename}...")
    if default_dir not in filename:
        if len(os.path.join(default_dir, filename))>=len(default_dir)+len(filename):
            filename = os.path.join(default_dir, filename)
        else:
            filename = default_dir+ filename
    # Create parent directories if they don't exist
    parent_dir = os.path.dirname(f"{filename}")
    os.makedirs(parent_dir, exist_ok=True)
    return f"File {filename} appended successfully"

def read_file(filename,default_dir,improve):
    print("===========READ FILE==============")
    filename = safepath(filename,default_dir,improve)
    if default_dir not in filename:
        if len(os.path.join(default_dir, filename))>=len(default_dir)+len(filename):
            filename = os.path.join(default_dir, filename)
        else:
            filename = default_dir+ filename
    print(f"FUNGSI: Reading file {filename}...")
    if not os.path.exists(f"{filename}"):
        print(f"File {filename} does not exist")
        return f"File {filename} does not exist"
    with open(f"{filename}", "r") as f:
        content = f.read()
    return f"The contents of '{filename}':\n{content}"

def browser_search(query,default_dir,improve):
    print(f"Searching for : '{query}'")
    url = "https://api.catto.tech/v1/chat/completions"

    # Replace <token> with your API token
    headers = {
        "Authorization": "Bearer "+os.getenv("openai_key"),
        "Content-Type": "application/json"
    }

    params = {
        "model": "bard",
        "messages": [
            {"role": "user", "content": query},
        ],
    }
    response=""
    try:
        response = requests.post(url, json=params, headers=headers)
    except:
        print(params)
    print(response.status_code)
    if(response.status_code==200):
        hasil=response.json()
        print(hasil)
        return hasil['choices'][0]['message']['content']
    else:
        return "Searching Fail ..."

def create_dir(directory,default_dir,improve):
    directory = safepath(directory,default_dir,improve)
    if default_dir not in directory:
        if len(os.path.join(default_dir, directory))>=len(default_dir)+len(directory):
            directory = os.path.join(default_dir, directory)
        else:
            directory = default_dir+ directory
    print(f"FUNGSI: Membuat Folder {directory}")
    if os.path.exists( directory ):
        return "ERROR: Directory exists"
    else:
        os.mkdir( directory )
        return f"Directory {directory} created!"

def move_file(source, destination,default_dir,improve):
    source = safepath(source,default_dir,improve)
    destination = safepath(destination,default_dir,improve)
    if default_dir not in source:
        if len(os.path.join(default_dir, source))>=len(default_dir)+len(source):
            source = os.path.join(default_dir, source)
        else:
            source = default_dir+ source
    if default_dir not in destination:
        if len(os.path.join(default_dir, destination))>=len(default_dir)+len(destination):
            destination = os.path.join(default_dir, destination)
        else:
            destination = default_dir+ destination
    print(f"FUNGSI: Move {source} to {destination}...")
    # if input("ARE YOU SURE TO MOVE THAT ? y/(n)") or "n" =="y":
        # Create parent directories if they don't exist
    parent_dir = os.path.dirname(f"{destination}")
    os.makedirs(parent_dir, exist_ok=True)

    try:
        shutil.move(f"{source}", f"{destination}")
    except:
        if os.path.isdir(f"{source}") and os.path.isdir(f"{destination}"):
            return "ERROR: Destination folder already exists."
        return "Unable to move file."

    return f"Moved {source} to {destination}"
    # else:
    #     return f"Cancel to Move {source} to {destination}"

def copy_file(source, destination,default_dir,improve):
    source = safepath(source,default_dir,improve)
    destination = safepath(destination,default_dir,improve)
    if default_dir not in source:
        if len(os.path.join(default_dir, source))>=len(default_dir)+len(source):
            source = os.path.join(default_dir, source)
        else:
            source = default_dir+ source
    if default_dir not in destination:
        if len(os.path.join(default_dir, destination))>=len(default_dir)+len(destination):
            destination = os.path.join(default_dir, destination)
        else:
            destination = default_dir+ destination

    print(f"FUNGSI: Copy {source} to {destination}...")
    # if input("ARE YOU SURE TO MOVE THAT ? y/(n)") or "n" =="y":
        # Create parent directories if they don't exist
    parent_dir = os.path.dirname(f"{destination}")
    os.makedirs(parent_dir, exist_ok=True)
    try:
        shutil.copy(f"{source}", f"{destination}")
    except:
        if os.path.isdir(f"{source}") and os.path.isdir(f"{destination}"):
            return "ERROR: Destination folder already exists."
        return "Unable to copy file."

    return f"File {source} copied to {destination}"
    # else:
        # return f"Cancel to File {source} copied to {destination}"

def delete_file(filename,default_dir,improve):
    filename = safepath(filename,default_dir,improve)
    if default_dir not in filename:
        if len(os.path.join(default_dir, filename))>=len(default_dir)+len(filename):
            filename = os.path.join(default_dir, filename)
        else:
            filename = default_dir+ filename
    print(f"FUNGSI: Deleting file {filename}")
    path = f"{filename}"
    if input("ARE YOU SURE TO MOVE THAT ? y/(n)") or "n" =="y":
        if not os.path.exists(path):
            print(f"File {filename} does not exist")
            return f"ERROR: File {filename} does not exist"

        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except:
            return "ERROR: Unable to remove file."

        return f"File {filename} successfully deleted"
    else:
        return f"Cancel to File {filename} successfully deleted"

def list_files(list = "", print_output = True,default_dir="code",improve=False):
    files_by_depth = {}

    for root, _, filenames in os.walk(default_dir):
        depth = str(root[len(default_dir):].count(os.sep))

        for filename in filenames:
            file_path = os.path.join(root, filename)
            if depth not in files_by_depth:
                files_by_depth[depth] = []
            files_by_depth[depth].append(file_path)

    files = []
    counter = 0
    max_files = 20
    for level in files_by_depth.values():
        for filename in level:
            counter += 1
            if counter > max_files:
                break
            files.append(filename)

    # Remove "code/" from the beginning of file paths
    files = [file_path.replace(default_dir, "", 1) for file_path in files]

    if print_output: print(f"FUNGSI: Files in {default_dir} directory:\n{files}")
    return files

def ask_clarification(question,default_dir,improve):
    # answer = input(f"## ChatGPT Asks a Question ##\n```{question}```\nAnswer: ")
    return question

def yesno(prompt, answers = ["y", "n"]):
    answer = ""
    while answer not in answers:
        slash_list = '/'.join(answers)
        answer = input(f"{prompt} ({slash_list}): ")
        if answer not in answers:
            or_list = "' or '".join(answers)
            print(f"Please type '{or_list}'")
    return answer

def run_cmd(base_dir, command, reason,default_dir,improve):
    base_dir = safepath(base_dir,default_dir,improve)
    print("FUNGSI: Run a command")
    print("## ChatGPT wants to run a command! ##")

    command = f"cd {default_dir}/" + base_dir.strip("/") + "; " + command
    print(f"Command: `{command}`")
    print(f"Reason: `{reason}`")

    answer = yesno(
        "Do you want to run this command?",
        ["YES", "NO"]
    )

    if answer == "YES":
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout + result.stderr
        return_value = "Result from command (last 245 chars):\n" + output[-245:]
        print(return_value)
        return return_value
    else:
        return "I don't want you to run that command"

def project_finished(finished,default_dir,improve):
    return "PROJECT_FINISHED"

def safepath(path,default_dir,improve):
    base = os.path.abspath(default_dir)
    if len(os.path.join(base, path))>=len(base)+len(path):
        file = os.path.abspath(os.path.join(base, path))
    else:
        file = os.path.abspath(base+ path)
    print("Path : "+file)
    if os.path.commonpath([base, file]) != base:
        print("ERROR: Tried to access file outside of code/ folder!")
        sys.exit(1)

    return path

# Function definitions for ChatGPT

definitions = [
    {
        "name": "list_files",
        "description": "List the files in the current project",
        "parameters": {
            "type": "object",
            "properties": {
                "list": {
                    "type": "string",
                    "description": "Set always to 'list'",
                },
            },
            "required": ["list"],
        },
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file with given name. Returns the file contents as string.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The filepath and filename to read",
                },
            },
            "required": ["filename"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file with given name. Existing files will be overwritten. Parent directories will be created if they don't exist. Content of file will be asked in the next prompt.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The filepath and filename  to write to",
                },
            },
            "required": ["filename"],
        },
    },
     {
        "name": "write_documentation",
        "description": "Write documentation content to a file with given name. Existing files will be overwritten. Parent directories will be created if they don't exist. Content of file will be asked in the next prompt. Only use this function if user ask want to a documentation",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The filepath and filename  to write to",
                },
            },
            "required": ["filename"],
        },
    },
    # {
    #     "name": "append_file",
    #     "description": "Write content to the end of a file with given name",
    #     "parameters": {
    #         "type": "object",
    #         "properties": {
    #             "filename": {
    #                 "type": "string",
    #                 "description": "The filepath and filename to write to",
    #             },
    #             "content": {
    #                 "type": "string",
    #                 "description": "The content to write into the file",
    #             },
    #         },
    #         "required": ["filename", "content"],
    #     },
    # },
    {
        "name": "replace_file",
        "description": "Replace some of the content in the file with given name, make sure to replace just only the part that it need to be replace and not make a error loop in the code. good example = (filename : styles.css (replace : #task-list {\n  list-style: none;\n}\n.task-item{\n  font-size: 11;\n}) (content : #task-list {\n  list-style: square;\n}\n.task-item{\n  font-size: 13;\n  color: #555;\n})",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The filepath and filename  to write to",
                },
                "replace": {
                    "type": "string",
                    "description": "The some content of the file that will be replace",
                },
                "content": {
                    "type": "string",
                    "description": "The content to replace into the file",
                },
            },
            "required": ["filename", "replace", "content"],
        },
    },
    {
        "name": "move_file",
        "description": "Move a file from one place to another. Parent directories will be created if they don't exist",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "The source file to move",
                },
                "destination": {
                    "type": "string",
                    "description": "The new filename / filepath",
                },
            },
            "required": ["source", "destination"],
        },
    },
    {
        "name": "create_dir",
        "description": "Create a directory with given name",
        "parameters": {
            "type": "object",
            "properties": {
                "directory": {
                    "type": "string",
                    "description": "Name of the directory to create",
                },
            },
            "required": ["directory"],
        },
    },
    {
        "name": "copy_file",
        "description": "Copy a file from one place to another. Parent directories will be created if they don't exist",
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "The source file to copy",
                },
                "destination": {
                    "type": "string",
                    "description": "The new filename / filepath",
                },
            },
            "required": ["source", "destination"],
        },
    },
    {
        "name": "browser_search",
        "description": "To search the web using browser google search engine",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query that use to look for the infomations",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "delete_file",
        "description": "Deletes a file with given name",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The filename to delete",
                },
            },
            "required": ["filename"],
        },
    },
     {
        "name": "reset_memory",
        "description": "Reset memory of previous response of chat, use this function only if the user ask for reset memory",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to ask the user",
                },
            },
            "required": ["question"],
        },
    },
    {
        "name": "ask_clarification",
        "description": "Ask the user a clarifying question about the project. Returns the answer by the user as string",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to ask the user",
                },
            },
            "required": ["question"],
        },
    },
    {
        "name": "project_finished",
        "description": "Call this function when the project is finished",
        "parameters": {
            "type": "object",
            "properties": {
                "finished": {
                    "type": "string",
                    "description": "Set this to 'finished' always",
                },
            },
            "required": ["finished"],
        },
    },
    {
        "name": "run_cmd",
        "description": "Run a terminal command. Returns the output.",
        "parameters": {
            "type": "object",
            "properties": {
                "base_dir": {
                    "type": "string",
                    "description": "The directory to change into before running command",
                },
                "command": {
                    "type": "string",
                    "description": "The command to run",
                },
                "reason": {
                    "type": "string",
                    "description": "A reason for why the command should be run",
                },
            },
            "required": ["base_dir", "command", "reason"],
        },
    },
]
