# PyPrediktorEdgeClient
A Python library to talk to Prediktor APIS/EDGE


## Installation
To install, run this command: 
```
pip install git+https://github.com/PrediktorAS/PyPrediktorEdgeClient.git
```

If you get an `OSError: [WinError 5] Access is denied` on Windows, try to run 
```
pip install git+https://github.com/PrediktorAS/PyPrediktorEdgeClient.git --user
```

## Usage
In your code, use:
`from pyprediktoredgeclient import hive`

## To set up a development env
First create a venv for this project: cd `<this folder>`

`python -m venv .venv`

This will create the folder .venv in you project (ignored by gitignore)

Activate your venv:
`.venv\Scripts\activate`
or on macos:
`source .venv/bin/activate`

Install/update dependencies:  
`pip install -r requirements.txt`

