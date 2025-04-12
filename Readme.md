# Triathlon Scheduling Software

## Intro

This is an experiment in using linear programming to create a triathlon training schedule. It is very much a work in progress and is the first time I am working with linear programming and the pyomo framework. My goal is to allow for a simple set of input parameters to generate a training schedule to prepare an athlete for a triathlon scheduled on a specified date. Training plans are inspired by [The Triathlete's Training Bible](https://www.amazon.com/Triathletes-Training-Bible-Worlds-Comprehensive/dp/1937715442) (4th Edition) by Joe Friel.

NOTE: Please do not use this for training advice. It is an experiment in software technique and has not been tested for use.

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

## The Model

This schedule creator uses a two step process. 

### Step 1

First, the start date and event date from the incoming configuration are used to establish the set of available weeks. These weeks are assigned a strategy and weeks starting new blocks are established following a [linear periodization](https://en.wikipedia.org/wiki/Sports_periodization) approach.

### Step 2

Second, each day in the weeks defined in Step 1 are assigned workouts for swim, bike, and run.

The objective of each week is to maximize the total fitness increase across the three sports during the week.

With d = day of of week, w = workout identifier and m = total number of workouts, the following objective function is maximized:

$$\sum_{w=0}^m \sum_{d=0}^6 FitnessIncrease[w]*SelectedWorkout[d, w]$$

This model is subject to the following constraints:

#### Constraint 1: There should be no more than 2 workouts per day.

$$\forall 0 \leq d \leq 6 \sum_{w=0}^m SelectedWorkout[d, w] \leq 2$$

TODO: other constraints
 

## TODO List

I intend to continue work on this project in the near future. Next steps include:
* Add documentation of objective function and constraints.
* Create docker image to ease sharing/deployment.
* Better separation of concerns in files, initial weekly plan out of jupyter notebook.
* Update input and output formats to be easier to use.
* Add unit tests.