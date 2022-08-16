# Thisted project - Speech service
This will server Text-to-Speech (TTS) and Speech-to-Text (STT) endpoints.

Currently the intent is to use the Google API

## Requirements
Python 3.6+

## Installation
Install the required packages in your local environment
```bash
conda env create --name thisted_speech_env --file environment.yml
``` 
Note: conda allows us to install both pip and conda packages which solves some install challenges on for instance the Windows platform.

## Running backend app
```bash
uvicorn thisted_speech.app.main:app
```

Note the service requires a Google cloud credentials file "credentials.json" - this is not included in repository.

