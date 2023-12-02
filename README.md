# gptc
Generative Pre-trained Traffic Control: using LLMs for air traffic control

## Installation
This code is written as a plugin for the BlueSky ATC simulator. 

Running `install.sh` will place the necessary files in your BlueSky plugin directory if `bluesky-simulator` is installed as a package. 
For other installation methods, you will have to manually place the files in the correct directory. 

Edit the BlueSky configuration file to enable the plugin.

You will need a `.env` file specifying your LLM API access key and related information. 
The plugin currently expects the use of the University of Michigan ChatGPT API.

## Use

In the simulator, use `gptc on` and `gptc off` to toggle the activity of the plugin. 
The default state is off.