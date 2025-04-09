# this first version was too open ended


import csv
import pyomo.environ as pyo
import datetime

def add_workouts_to_week_plan(week, incoming_fatigue, incoming_fitness, is_last_week_of_block, weekly_hours_max):
    workouts = [{}] * 7

    # initialize weekly planning model
    model = pyo.ConcreteModel()

    model.IncomingFitness = incoming_fitness
    model.IncomingFatigue = incoming_fatigue

    model.FatigueUpperBound = 90 # upper limit to fatigue for all sports

    
    model.IntensityCoefficient = 3
    model.DurationCoefficient = 2
    model.FatigueCoefficient = -.5
    model.WeeklyHoursMax = weekly_hours_max

    if week["strategy"] == "base":
        model.IntensityCoefficient = 1
        model.DurationCoefficient = 3
        model.FatigueCoefficient = -.5
    elif week["strategy"] == "peak" or is_last_week_of_block:
        model.IntensityCoefficient = 1
        model.DurationCoefficient = 1
        model.FatigueCoefficient = -5
        model.WeeklyHoursMax = weekly_hours_max * .5
    
    model.Days = pyo.RangeSet(0,6) # days of the week
    model.M = 5000 # large number
    # vars for bike, run, swim workouts
    
    model.HasBikeWorkout = pyo.Var(model.Days, domain=pyo.Boolean)
    model.HasRunWorkout = pyo.Var(model.Days, domain=pyo.Boolean)
    model.HasSwimWorkout = pyo.Var(model.Days, domain=pyo.Boolean)

    intensity_upper_bound = 10
    if week["strategy"] == "base":
        intensity_upper_bound = 5
    
    model.BikeWorkoutIntensities = pyo.Var(model.Days, domain=pyo.NonNegativeIntegers, bounds=(0, intensity_upper_bound))
    model.RunWorkoutIntensities = pyo.Var(model.Days, domain=pyo.NonNegativeIntegers, bounds=(0, intensity_upper_bound))
    model.SwimWorkoutIntensities = pyo.Var(model.Days, domain=pyo.NonNegativeIntegers, bounds=(0, intensity_upper_bound))
        
    model.BikeWorkoutDurations = pyo.Var(model.Days, domain=pyo.NonNegativeIntegers, bounds=(0, 120)) # in minutes
    model.RunWorkoutDurations = pyo.Var(model.Days, domain=pyo.NonNegativeIntegers, bounds=(0, 120))
    model.SwimWorkoutDurations = pyo.Var(model.Days, domain=pyo.NonNegativeIntegers, bounds=(0, 120))

    # add objective
    objective_day_range = range(0,7)
    fatigue_day_range = range(4,7)
    model.obj = pyo.Objective(expr=model.IntensityCoefficient*sum(model.BikeWorkoutIntensities[d] + model.RunWorkoutIntensities[d] + model.SwimWorkoutIntensities[d] for d in objective_day_range) + model.DurationCoefficient*sum(model.BikeWorkoutDurations[d] + model.RunWorkoutDurations[d] + model.SwimWorkoutDurations[d] for d in objective_day_range)+model.FatigueCoefficient*sum(model.BikeWorkoutIntensities[d] + model.RunWorkoutIntensities[d] + model.SwimWorkoutIntensities[d] for d in fatigue_day_range), sense=pyo.maximize)


    # add constraints

    # rule constraining to two workouts per day
    def two_workouts_per_day_rule(m, day):
        return m.HasBikeWorkout[day] + m.HasRunWorkout[day] + m.HasSwimWorkout[day] <=2

    model.two_workouts_per_day_constraint = pyo.Constraint(model.Days, rule=two_workouts_per_day_rule)
   
    # constraints that zero in Has__Workout must match with __WorkoutIntensities

    def must_match_workout_exists_with_intensity_rule_bike(m, day):
        return m.HasBikeWorkout[day] * model.M >= m.BikeWorkoutIntensities[day]

    model.must_match_workout_exists_with_intensity_constraint_bike = pyo.Constraint(model.Days, rule=must_match_workout_exists_with_intensity_rule_bike)

    def must_match_workout_exists_with_intensity_rule_run(m, day):
        return m.HasRunWorkout[day] * model.M >= m.RunWorkoutIntensities[day]

    model.must_match_workout_exists_with_intensity_constraint_run = pyo.Constraint(model.Days, rule=must_match_workout_exists_with_intensity_rule_run)

    def must_match_workout_exists_with_intensity_rule_swim(m, day):
        return m.HasSwimWorkout[day] * model.M >= m.SwimWorkoutIntensities[day]

    model.must_match_workout_exists_with_intensity_constraint_swim = pyo.Constraint(model.Days, rule=must_match_workout_exists_with_intensity_rule_swim)

    # the inverse of the above - there's got to be a better way to do this - TODO: research
    
    def must_match_workout_exists_with_intensity_rule_bike_2(m, day):
        return m.BikeWorkoutIntensities[day] * model.M >= m.HasBikeWorkout[day]

    model.must_match_workout_exists_with_intensity_constraint_bike_2 = pyo.Constraint(model.Days, rule=must_match_workout_exists_with_intensity_rule_bike_2)

    def must_match_workout_exists_with_intensity_rule_run_2(m, day):
        return m.RunWorkoutIntensities[day] * model.M >= m.HasRunWorkout[day]

    model.must_match_workout_exists_with_intensity_constraint_run_2 = pyo.Constraint(model.Days, rule=must_match_workout_exists_with_intensity_rule_run_2)

    def must_match_workout_exists_with_intensity_rule_swim_2(m, day):
        return m.SwimWorkoutIntensities[day] * model.M >= m.HasSwimWorkout[day]

    model.must_match_workout_exists_with_intensity_constraint_swim_2 = pyo.Constraint(model.Days, rule=must_match_workout_exists_with_intensity_rule_swim_2)

    
    # constraints that zero in Has__Workout must match with __WorkoutDurations
    
    def must_match_workout_exists_with_duration_rule_bike(m, day):
        return m.HasBikeWorkout[day] * model.M >= m.BikeWorkoutDurations[day]

    model.must_match_workout_exists_with_duration_constraint_bike = pyo.Constraint(model.Days, rule=must_match_workout_exists_with_duration_rule_bike)

    def must_match_workout_exists_with_duration_rule_run(m, day):
        return m.HasRunWorkout[day] * model.M >= m.RunWorkoutDurations[day]

    model.must_match_workout_exists_with_duration_constraint_run = pyo.Constraint(model.Days, rule=must_match_workout_exists_with_duration_rule_run)

    def must_match_workout_exists_with_duration_rule_swim(m, day):
        return m.HasSwimWorkout[day] * model.M >= m.SwimWorkoutDurations[day]

    model.must_match_workout_exists_with_duration_constraint_swim = pyo.Constraint(model.Days, rule=must_match_workout_exists_with_duration_rule_swim)

    # the inverse for durations - see note above - there's got to be a better way
    def must_match_workout_exists_with_duration_rule_bike_2(m, day):
        return m.BikeWorkoutDurations[day] * model.M >= m.HasBikeWorkout[day]

    model.must_match_workout_exists_with_duration_constraint_bike_2 = pyo.Constraint(model.Days, rule=must_match_workout_exists_with_duration_rule_bike_2)

    def must_match_workout_exists_with_duration_rule_run_2(m, day):
        return m.RunWorkoutDurations[day] * model.M >= m.HasRunWorkout[day]

    model.must_match_workout_exists_with_duration_constraint_run_2 = pyo.Constraint(model.Days, rule=must_match_workout_exists_with_duration_rule_run_2)

    def must_match_workout_exists_with_duration_rule_swim_2(m, day):
        return m.SwimWorkoutDurations[day] * model.M >= m.HasSwimWorkout[day]

    model.must_match_workout_exists_with_duration_constraint_swim_2 = pyo.Constraint(model.Days, rule=must_match_workout_exists_with_duration_rule_swim_2)

    # durations for workouts that exist should be longer than 20 minutes

    def must_have_min_duration_rule_swim(m, day):
        return m.SwimWorkoutDurations[day]  >= m.HasSwimWorkout[day]*20

        
    model.must_have_min_duration_constraint_swim = pyo.Constraint(model.Days, rule=must_have_min_duration_rule_swim)

    def must_have_min_duration_rule_bike(m, day):
        return m.BikeWorkoutDurations[day]  >= m.HasBikeWorkout[day]*20
        
    model.must_have_min_duration_constraint_bike = pyo.Constraint(model.Days, rule=must_have_min_duration_rule_bike)
        
    def must_have_min_duration_rule_run(m, day):
        return m.RunWorkoutDurations[day]  >= m.HasRunWorkout[day]*20

    model.must_have_min_duration_constraint_run = pyo.Constraint(model.Days, rule=must_have_min_duration_rule_run)

    
    
    # must not exceed fatigue by sport

    # approach:  5 day finite impulse response - with variable linear decay
    # note: no overall fatigue leads to bunching
    fatigue_rate = 7
    fatigue_decay_rate = 1.5
    fatigue_today = 5
    fatigue_window_size = 5
    incoming_fatigue_rate = 1.5

    def coefs_for_days(day):
        day_coefs = []
        for d in range(0,day):
            if day-d >= fatigue_window_size:
                day_coefs.append(0)
            else:
                day_coefs.append(fatigue_rate - fatigue_decay_rate*(day-d)) # coefficients stable
        return day_coefs

    def coef_for_incoming(day):
        if day > fatigue_window_size:
            return 0
        else:
            return ((fatigue_window_size - day)/fatigue_window_size)*incoming_fatigue_rate

    def must_not_exceed_fatigue_rule_bike(m,day):
        if day == 0:
            return m.IncomingFatigue["bike"] + m.BikeWorkoutIntensities[day] <= model.FatigueUpperBound
        else:
            day_range = range(0,day)
            day_coefs = coefs_for_days(day)
            incoming_coef = coef_for_incoming(day)
            return m.IncomingFatigue["bike"]*incoming_coef + sum(m.BikeWorkoutIntensities[d]*day_coefs[d] for d in day_range) + m.BikeWorkoutIntensities[day]*fatigue_today <= model.FatigueUpperBound
    
    model.must_not_exceed_fatigue_rule_bike = pyo.Constraint(model.Days, rule=must_not_exceed_fatigue_rule_bike)


    def must_not_exceed_fatigue_rule_run(m,day):
        if day == 0:
            return m.IncomingFatigue["run"] + m.RunWorkoutIntensities[day] <= model.FatigueUpperBound
        else:
            day_range = range(0,day)
            day_coefs = coefs_for_days(day)
            incoming_coef = coef_for_incoming(day)
            return m.IncomingFatigue["run"]*incoming_coef + sum(m.RunWorkoutIntensities[d]*day_coefs[d] for d in day_range) + m.RunWorkoutIntensities[day]*fatigue_today <= model.FatigueUpperBound
    
    model.must_not_exceed_fatigue_rule_run = pyo.Constraint(model.Days, rule=must_not_exceed_fatigue_rule_run)

    def must_not_exceed_fatigue_rule_swim(m,day):
        if day == 0:
            return m.IncomingFatigue["swim"] + m.SwimWorkoutIntensities[day] <= model.FatigueUpperBound
        else:
            day_range = range(0,day)
            day_coefs = coefs_for_days(day)
            incoming_coef = coef_for_incoming(day)
            return m.IncomingFatigue["swim"]*incoming_coef + sum(m.SwimWorkoutIntensities[d]*day_coefs[d] for d in day_range) + m.SwimWorkoutIntensities[day]*fatigue_today <= model.FatigueUpperBound
    
    model.must_not_exceed_fatigue_rule_swim = pyo.Constraint(model.Days, rule=must_not_exceed_fatigue_rule_swim)


    # intense workouts should be short

    intensity_multiplier = 20

    def must_be_short_if_intense_rule_bike(m,day):
        return m.BikeWorkoutIntensities[day]*intensity_multiplier + m.BikeWorkoutDurations[day] <= 50+m.IncomingFitness["bike"]*2

    model.must_be_short_if_intense_rule_bike = pyo.Constraint(model.Days, rule=must_be_short_if_intense_rule_bike)
    
    def must_be_short_if_intense_rule_swim(m,day):
        return m.SwimWorkoutIntensities[day]*intensity_multiplier + m.SwimWorkoutDurations[day] <= 50+m.IncomingFitness["swim"]*2 
        
    model.must_be_short_if_intense_rule_swim = pyo.Constraint(model.Days, rule=must_be_short_if_intense_rule_swim)

    def must_be_short_if_intense_rule_run(m,day):
        return m.RunWorkoutIntensities[day]*intensity_multiplier + m.RunWorkoutDurations[day] <= 50+m.IncomingFitness["run"]*2 
        
    model.must_be_short_if_intense_rule_run = pyo.Constraint(model.Days, rule=must_be_short_if_intense_rule_run)


        


    # must not exceed weekly duration limit

    def must_not_exceed_weekly_time_limit_rule(m):
        return sum(m.BikeWorkoutDurations[d] + m.RunWorkoutDurations[d] + m.SwimWorkoutDurations[d] for d in m.Days) <= model.WeeklyHoursMax*60 

    model.must_not_exceed_weekly_time_limit = pyo.Constraint(rule=must_not_exceed_weekly_time_limit_rule)

    
    # solve
    solver = pyo.SolverFactory('glpk')
    solver.options['tmlim'] = 10
    results = solver.solve(model)
    
    # print results
    # print(results)
    # model.pprint()
    
    #parse results and add workouts to week


    for day in model.Days:
        workout = {}
        if model.HasRunWorkout[day].value == 1:
            workout["run"] = { "day": day, "intensity": model.RunWorkoutIntensities[day].value, "duration": model.RunWorkoutDurations[day].value }
        if model.HasBikeWorkout[day].value == 1:
            workout["bike"] = { "day": day, "intensity": model.BikeWorkoutIntensities[day].value, "duration": model.BikeWorkoutDurations[day].value }
        if model.HasSwimWorkout[day].value == 1:
            workout["swim"] = { "day": day, "intensity": model.SwimWorkoutIntensities[day].value, "duration": model.SwimWorkoutDurations[day].value }
        workouts[day] = workout
    week["workouts"] = workouts


    fitness_multiplier = .005 # fitness accumulates slowly
    def fitness_gain(sport):
        match sport:
            case "run":
                return sum(model.RunWorkoutIntensities[day].value*model.RunWorkoutDurations[day].value*fitness_multiplier for day in model.Days)
            case "bike":
                return sum(model.BikeWorkoutIntensities[day].value*model.BikeWorkoutDurations[day].value*fitness_multiplier for day in model.Days)
            case "swim":
                return sum(model.SwimWorkoutIntensities[day].value*model.SwimWorkoutDurations[day].value*fitness_multiplier for day in model.Days)

    
    week["fitness_outcome"] = { 
        "run": incoming_fitness["run"]*.95 + fitness_gain("run"), # depreciate a bit of incoming fitness and add on gains
        "bike": incoming_fitness["bike"]*.95 + fitness_gain("bike"),
        "swim": incoming_fitness["swim"]*.95 + fitness_gain("swim")
    }


    def fatigue_outcome(sport):
        day_range = range(0,6)
        day_coefs = coefs_for_days(6)
        match sport:
            case "run":
                return sum(model.RunWorkoutIntensities[d].value*day_coefs[d] for d in day_range) 
            case "bike":
                return sum(model.BikeWorkoutIntensities[d].value*day_coefs[d] for d in day_range)
            case "swim":
                return sum(model.SwimWorkoutIntensities[d].value*day_coefs[d] for d in day_range)
    
    week["fatigue_outcome"] = {
        "run":  fatigue_outcome("run"),
        "bike": fatigue_outcome("bike"),
        "swim": fatigue_outcome("swim")
    }
    
    return week
