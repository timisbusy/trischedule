# Triathlon Scheduling Software

## Intro

This is an experiment in using linear programming to create a triathlon training schedule. It is very much a work in progress and is the first time I am working with linear programming and the pyomo framework. My goal is to allow for a simple set of input parameters to generate a training schedule to prepare an athlete for a triathlon scheduled on a specified date. Training plans are inspired by The Triathlete's Training Bible (4th Edition) by Joe Friel.

NOTE: Please do not use this for training advice

## Getting Started

```
virtualenv env

envstart

pip3 install --upgrade pip
pip3 install --upgrade jupyter matplotlib numpy pandas scipy scikit-learn
pip3 install --upgrade 'pyomo[optional]' 


jupyter notebook
```

You will also need to install `gplk` following instructions here: https://www.gnu.org/software/glpk/

## Next Steps

I intend to continue work on this project in the near future. Next steps include:
* Add documentation of objective function and constraints.
* Create docker image to ease sharing/deployment.
* Better separation of concerns in files, initial weekly plan out of jupyter notebook.
* Update input and output formats to be easier to use.
* Add unit tests.