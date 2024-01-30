# READ ME GROUP 20

Created by: SEN1211-ABM Group 20

|          Name           | Student Number |
|:-----------------------:|:--------|
|   Simone van der Boon   | 5086620 | 
| Martijntje van der Goes | 4907477 |
|  Matthijs van de Wiel   | 4896947 

### Getting started
The model uses the latest version of the following packages: Mesa, Pandas, Scipy, Matplotlib, Seaborn, networkx and rasterio
The Python Interpreter is set to Python 13.12. Make sure to install the necessary packages before trying to run the model.

## Introduction
This ReadMe file contains a high level explanation of how the model we have created for this course works. 
We give a general description of the model, how to use it and where to find certain information. More detailed parts on the coding
and how certain rules, actions and processes are structured can be found in markdowns in between the code in notebooks or with comments
in the code itself.

The report can be found under Report_vdBoon_5086620_vdWiel_4896947_vdGoes_4907477.pdf. 

## How to use
The model is structured so that the main model can be found in model.py. This file takes input data from directory input_data. 
Model.py imports the class Households from agents.py and uses certain functions from functions.py. In the Notebooks in the model directory
models are created and run individually or in a batch runner. The data produced by these notebooks is stored in output_data. The output_data 
is used in different notebooks that end with "... analysis". Some of these notebooks have produced useful figures for proper analysis in
the report. These are save as jpg in the results_figures directory. 

To create a model yourself, use the from model import AdaptationModel line at the start. This will access the model file and extract 
everything you need. This can be done either in a new Pycharm python file or Jupyter Notebook.

To run the model, there are two options. The model has a built-in model_run function that runs the model until a random number between 0
and the specified number_of_steps model parameter. This function is essential for running it with a batch runner. However, the model is 
also run with a simple for loop after the initialization of the model.

In order to visualize the model, one can open demo.ipynb Jupyter Notebook. The network of household agents is shown upon the floodmap that is
specified as model parameter. These visualizations are mainly to help understand the context of the model better. They are not used throughout
analyses and other documentation. 




