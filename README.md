# PyPrediktorEdgeClient
A Python library to talk to Prediktor APIS/EDGE


## Installation
IMPORTANT! This module is dependant on the PythonNet Module. If you are struggling with the install. Please try to install PythonNet on its own first:
```
pip install pythonnet
```
You'll also find more info on this at [The PythonNet Github page](https://github.com/pythonnet/pythonnet/wiki/Troubleshooting-on-Windows,-Linux,-and-OSX).

On Linux and MacOS, you need to have installed [Mono](https://www.mono-project.com/) first


To install this library, run this command: 
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

You'll find examples in the example folder

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

