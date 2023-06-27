### index.html
- head
    - title: 'Database Extractor'
    - link: 'styles.css' (CSS styling for the frontend)
- body
    - form: ID 'database-form'
        - input: name 'database_name', placeholder 'Enter database name'
        - button: ID 'submit-btn', text 'Extract Database'
    - script: 'app.js' (Frontend JavaScript)

### styles.css
- **Selectors, Id, Classes, Properties, and Values**
  - body: font-family, background-color
  - #database-form: display, flex-direction, align-items, justify-content
  - input: margin-right, border, border-radius, padding
  - #submit-btn: cursor, padding, background-color, color, border, border-radius

### app.js
- Variables
  - databaseForm: DOM form element (ID 'database-form')
  - databaseNameInput: DOM input element (name 'database_name')
- Event listeners
  - databaseForm (submit)
    - Output: Send a POST request to the backend `/create-database` route with the database name
- Functions & Methods
  - postData():
    - Input: url (string), data (object)
    - Output: Send a POST request to the given url with the given data

### app.py
- Global Variables
  - app: Flask instance
- Routes
  - '/': GET request, render index.html
  - '/create-database': POST request, process the extraction and save to JSON file
- Functions & Methods
  - create_database():
    - Input: None
    - Output: Extract database details and save to JSON file, return a response

### database_connector.py
- Global Variables
  - connection: None (initially, will be replaced with a connection object)
- Functions & Methods
  - connect_to_database(database_name):
    - Input: database_name (string)
    - Output: Connect to the specified database_name and return a connection object
  - extract_database_details(connection):
    - Input: connection (MySQL connection object)
    - Output: Extract all tables, fields, primary keys, and example data as a list of JSON objects
  - save_to_file(database_name, data):
    - Input: database_name (string), data (JSON object)
    - Output: Save the data to a file named `<database_name>.json`

### requirements.txt
- Flask
- MySQL-connector-python

### Interconnections between files
- app.py (create_database) -> database_connector.py (connect_to_database, extract_database_details, save_to_file)

### UIX Description and App Behavior
- The user inputs the database name into the form input on the frontend
- When the form is submitted, a POST request is sent to the backend `/create-database` route
- The backend connects to the specified database, extracts the required details, and saves them to a JSON file

### Libraries(connections)
- Flask (web framework)
- MySQL-connector-python (MySQL database connector)

### Improvement Ideas
- Add error handling for invalid database names or connection errors
- Allow the user to specify the server IP, username, and password for the MySQL connection
- Implement a loading indicator while the extraction is in progress

### ETC
- The frontend and backend are responsible for receiving user input and processing the database extraction, respectively
- The shared dependencies are maintained and organized according to their respective roles in the application