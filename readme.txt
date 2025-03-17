to use:
- create virtual environment using venv


DEBUGGING
to debug, create a launch.json with the following configuration:
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Debug bean-extract",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/venv/bin/bean-extract",  // Adjust the path to bean-extract
            "args": [
                "config.py",
                "umsaetze_9787183916_20250313-1227.csv"
            ],
            "console": "integratedTerminal",
            "justMyCode": false,
            "env": {
                "PYTHONPATH": "${workspaceFolder}/importers"  // Adjust the path to your importers
            }
        }
    ]
}

In a similar way bean-identify can also be debugged.

COMDIRECT 
For the exported CSV files, make sure that you do not edit them in a text editor. This may change the encoding of the file in such a way as to cause problems with the encoding of the german characters.

