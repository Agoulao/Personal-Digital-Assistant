# Personal Digital Assistant

Code developed for my Master's Thesis entitled: 

### *Assistente digital baseado em Inteligência Artificial para PC* (*Artificial Intelligence-based digital assistant for PC*)

Master's in Computer Science and Computer Engineering at [Lisbon School of Engineering (ISEL)](https://www.isel.pt/en), 2025

This project presents a modular Windows desktop application designed to act as a personal digital assistant. \
It supports both voice commands and text input, allowing users to interact with their computer and various online services through natural language. \
The core of the assistant is built with extensibility in mind, leveraging a pluggable Large Language Model (LLM) adapter and specialized functionality modules.

The full thesis is present [here](https://github.com/Agoulao/Personal-Digital-Assistant/blob/main/thesis). \
Associated scientific publications include:

* António Goulão, Dinis Dias, Artur Ferreira, and Nuno Leite, \
*“A Personal Digital Assistant Enhanced with Artificial Intelligence Techniques”*,  
Simpósio em Informática (INForum), September 2025, Évora, Portugal. \
[Avaliable on ResearchGate](https://www.researchgate.net/publication/395268319_A_Personal_Digital_Assistant_Enhanced_with_Artificial_Intelligence_Techniques)

* António Goulão, Dinis Dias, Artur Ferreira, and Nuno Leite, \
“A Modular Digital Assistant for Windows with Large Language Models”, \
Portuguese Conference on Pattern Recognition (RECPAD), October 2025, Aveiro, Portugal. \
[Avaliable on ResearchGate](https://www.researchgate.net/publication/397138243_A_Modular_Digital_Assistant_for_Windows_with_Large_Language_Models)

## Features

* **Natural Language Understanding:** Interprets user commands via an integrated LLM (Google Gemini API, Meta LLaMA).

* **Voice Interaction:**

    * **Automatic Speech Recognition (ASR):** Utilizes `SpeechRecognition` (Google's Chrome Speech API) for accurate speech-to-text conversion with noise calibration.

    * **Text-to-Speech (TTS):** Employs `pyttsx3` for offline text-to-speech, ensuring responsive voice output.

* **Graphical User Interface (GUI):** A responsive desktop interface built with `PyQt5`.

* **Modular Architecture:** Easily extendable with new functionalities through a pluggable module system.

* **Core Functionality Modules:**

  * **Operating System Automation:** Manages files and folders, opens applications and controls mouse and keyboard.

  * **Gmail Integration:** Read, send, and manage emails via Gmail API.
  
  * **Schedule and Task Management:** Integrates with Google Calendar API

## Setup and Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```

2.  **Ensure Python 3.10 is installed.**

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

Before running the application, you need to configure API keys for the LLM and other services.

1.  **Open `config.py`** in the project directory.

2.  **Update API Keys:**

    * For Google Gemini API, replace `"YOUR_GEMINI_API_KEY"` with your actual API key.

    * If using other LLM providers (e.g., Awan, Novita), ensure `YOUR_[PROVIDER]_API_KEY` is set correctly and update their respective API keys.

## Google Calendar Integration and Gmail Setup

For Google Calendar and Gmail functionality, you need to obtain OAuth 2.0 credentials:

1.  **Navigate to Google Cloud Console:** `https://console.cloud.google.com`

2.  **Create a new project** (or select an existing one).

3.  **Enable the Google Calendar API and Gmail API** for your project.

4.  **Create OAuth 2.0 Client ID credentials:**

    * Go to "APIs & Services" > "Credentials".

    * Click "CREATE CREDENTIALS" > "OAuth client ID".

    * Select "Desktop app" as the application type.

    * Download the generated `client_secret-<something>.json` file.

5.  **Rename this downloaded file to `client_secret.json`** and place it in the `modules` directory of this project. This file is crucial for the application to authenticate with your Google Calendar and Gmail.

6.  **Add required OAuth scopes:**

    * Go to **APIs & Services** > **OAuth consent screen**.  
    * Under **Scopes**, click **Add or Remove Scopes**.  
    * Add the following scopes:  
      - `https://mail.google.com/` – Full Gmail access or another gmail scope if you don't want to give full permission
      - `https://www.googleapis.com/auth/calendar.events` – Create, edit, and delete calendar events  
    * Save changes.  

## Running the Application

To start the Personal Digital Assistant, execute the `main.py` file:

```bash
python main.py
```

This will launch the graphical user interface, and you can begin interacting with the assistant via text input or voice commands (if your microphone is set up).