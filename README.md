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

To collect statistics, the `start_gptc_scenario <filename>` command allows for the running of the same scenario file as many times as needed. Just add this command as the last line in your scenario file, e.g. 

`00:07:57.00>start_gptc_scenario 740_heading_repeat.scn`

and the plugin will write out separation violation information to `scenario_results.txt`.

![Example of GPTC running in heading-only mode.](https://github.com/rgovindjee/gptc/blob/main/gptc_deconfliction.png?raw=true "Example of GPTC running in heading-only mode.")