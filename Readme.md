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

A variable `SelectedWorkouts` is defined with a binary value for each workout on each day. 1 means that the workout has been selected and 0 means that it has not. This is essentially a knapsack problem for each day, with constraints sometimes being applied to the day and other times across the week.

The two major factors in constraints and optimization are `fitness` and `fatigue`. Both of these parameters are assigned a value for each workout, whereby a workout increases both `fitness` and `fatigue`. Limits are placed around `fatigue` values, both on a daily basis and across the weeks. Both of these factors are passed forward between weeks.

---
**Note**

Fitness and fatigue measures are not based in any particular system. If this project evolves, it would be good to consider how excercise/sports science typically measures these features and benchmark to them.

---

The objective of each week is to maximize the total `fitness` increase across the three sports during the week. Each week, the total `fitness` increase for each sport is calculated and added to a slighly depreciated value of the incoming `fitness` value for that sport. This is similar to an infinite impulse response paradigm.

With `d` = day of of week, `w` = workout identifier and `m` = total number of workouts, the following objective function is maximized:

$$\sum_{w=0}^m \sum_{d=0}^6 FitnessIncrease[w]*SelectedWorkouts[d, w]$$

This model is subject to the following constraints:

#### Constraint 1: There should be no more than 2 workouts per day.

$$\forall \quad 0 \leq d \leq 6 \quad \sum_{w=0}^m SelectedWorkouts[d, w] \leq 2$$

#### Constraint 1a: There should be no more than 1 workout of each sport per day. 

For each sport's workouts $w_s$ up to $m_s$:

$$\forall \quad 0 \leq d \leq 6 \quad \sum_{w{_s}=0}^{m{_s}} SelectedWorkouts[d, w{_s}] \leq 1$$

#### Constraint 2: Fatigue must remain below maximum for each sport.

This constraint uses an approach similar to a finite impulse response to ensure that fatigue does not accumulate above a maximum level during the week. For each sport's workouts $`w_s`$ up to $`m_s`$ and each day of the week $`d`$ (Note rendering issue on constraint 2 and 2a. TODO: debug this further - rendering works in https://latexeditor.lagrida.com/):

$$\forall \quad 0 \leq d \leq 6 \quad with \quad d_0 = max(0,d-5) \quad IncomingFatigue_s * max(0,(1 - (d * .25))) \quad + \quad  \sum_{w{_s}=0}^{m{_s}} \quad \sum_{d{_i} = d{_0}}^d \quad FatigueIncrease[w{_s}] * SelectedWorkouts[d{_i}, w{_s}]  \leq FatigueUpperBound$$

#### Constraint 2a: Total fatigue across sports must remain below maximum.

This constraint is similar to constraint 2 but enforces a maximum fatigue level across the three sports. Note that `TotalFatigueUpperBound` is a higher value than `FatigueUpperBound`. A combination of sports can add up to more fatigue, but enforces a limit for what is, after all, a single athlete.

$$\forall \quad 0 \leq d \leq 6 \quad with \quad d_0 = max(0,d-5) \quad \sum_{s=0}^2 IncomingFatigue_s * max(0,(1 - (d * .25))) \quad + \quad  \sum_{w=0}^m \quad \sum_{d{_i} = d{_0}}^d \quad FatigueIncrease[w] * SelectedWorkouts[d{_i}, w]  \leq TotalFatigueUpperBound$$

#### Constraint 3: Must not exceed weekly maximum duration (training hours).

Training hours are user configurable, and the duration of weekly workouts should not exceed this limit. Workout durations are set in minutes, so we need to convert `WeeklyTrainingHoursLimit` to minutes

$$\sum_{d=0}^6 \sum_{w=0}^m WorkoutDuration[w] * SelectedWorkouts[d, w] \leq WeeklyTrainingHoursLimit * 60$$

#### Constraint 4: Fitness for sports should not diverge more than a configured amount.

---
**Note** 

This could become infeasible if the incoming fitness levels at the start are already too far diverged.
In this case, it would be good to ensure instead that the fitness levels are converging. This would bias workouts toward weaker sports.

---

This constraint compares two sports $`s_a`$ and $`s_b`$ for all combination of sports and ensures that the difference in fitness level at the end of the week does not exceed a set value. This approach ensures that the difference is in the range of `MaxDivergence` by exploiting the fact that $MaxDivergence + value \leq MaxDivergence * 2$, when enforced from both directions will act equivalently to $|value| \leq MaxDivergence$

$$MaxDivergence + ( IncomingFatigue[s_a]*FeedbackCoef + \sum_{d=0}^6 \sum_{w_{s_a}=0}^{m_{s_a}} SelectedWorkouts[d,{w_{s_a}}]*FitnessIncrease[{w_{s_a}}]*FitnessMultiplier) - (IncomingFatigue[s_b]*FeedbackCoef + \sum_{d=0}^6 \sum_{w_{s_b}=0}^{m_{s_b}} SelectedWorkouts[d,{w_{s_b}}]*FitnessIncrease[{w_{s_b}}]*FitnessMultiplier) \leq  MaxDivergence * 2 $$

#### Constraint 5: Must have variety in workouts - space out selection of the same workout
 
TODO: document this constraint.

## TODO List

I intend to continue work on this project in the near future. Next steps include:
- [ ] Complete documentation of variables, parameters, objective function, and constraints.
- [ ] Create docker image to ease sharing/deployment.
- [ ] Better separation of concerns in files, initial weekly plan out of jupyter notebook.
- [ ] Update input and output formats to be easier to use.
- [ ] Add unit tests.