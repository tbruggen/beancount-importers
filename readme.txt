to use:
- create virtual environment using venv

SAMPLE DATA (no real bank data needed)
- fake Comdirect CSV exports live in samples/ (account number 9999999999)
- they are committed to git (see .gitignore exceptions for samples/)
- try the importer on them:
    cp config.py.example config.py
    bean-extract config.py samples/umsaetze_9999999999_20240901-1606.csv
- run the integration tests against the samples:
    pytest tests/test_sample_data.py


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

