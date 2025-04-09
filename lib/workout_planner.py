import csv
import pyomo.environ as pyo
import datetime

from .workouts import workouts as workout_library



sport_to_int = {
    "swim": 0,
    "bike": 1,
    "run": 2
}


def add_workouts_to_week_plan(week, incoming_fatigue, incoming_fitness, is_last_week_of_block, weekly_hours_max):
    
    # import workout options from library

    available_workouts = workout_library.GetWorkoutsForWeek(week["strategy"])

    sport_dict = {}
    duration_dict = {}
    fatigue_increase_dict = {}
    fitness_increase_dict = {}

    swim_workouts = []
    bike_workouts = []
    run_workouts = []


    fitness_multiplier = 1 # fitness accumulates slowly

    for workout_id, workout_option in enumerate(available_workouts):
        sport_dict[workout_id] = sport_to_int[workout_option["sport"]]
        duration_dict[workout_id] = workout_option["duration"]
        fatigue_increase_dict[workout_id] = workout_option["fatigue_increase"]
        fitness_increase_dict[workout_id] = workout_option["fitness_increase"]

        match workout_option["sport"]:
            case "swim":
                swim_workouts.append(workout_id)
            case "bike":
                bike_workouts.append(workout_id)
            case "run":
                run_workouts.append(workout_id)

    # initialize weekly planning model
    model = pyo.ConcreteModel()

    model.IncomingFitness = incoming_fitness
    model.IncomingFatigue = incoming_fatigue

    model.FatigueUpperBound = 70 # upper limit to fatigue for each sports
    model.TotalFatigueUpperBound = 120 # upper limit to fatigue for all sports together

    model.WeeklyHoursMax = weekly_hours_max

    if week["strategy"] == "peak" or is_last_week_of_block:
        model.WeeklyHoursMax = weekly_hours_max * .5
    
    model.Days = pyo.RangeSet(0,6) # days of the week
    model.Sports = pyo.Set(initialize=["swim","bike","run"])
    model.WorkoutIds = pyo.RangeSet(0,len(available_workouts)-1)

    model.SelectedWorkouts = pyo.Var(model.Days, model.WorkoutIds, domain=pyo.Boolean)


    # objective: maximize fitness increase

    model.obj = pyo.Objective(expr=sum(fitness_increase_dict[workout_id]*model.SelectedWorkouts[(day,workout_id)] for day in model.Days for workout_id in model.WorkoutIds), sense=pyo.maximize)


    # constraints

    # constraint 1: no more than 2 workouts per day

    def max_workouts_per_day_rule(m, day):
        return sum(m.SelectedWorkouts[(day,workout_id)] for workout_id in m.WorkoutIds) <=2

    model.max_workouts_per_day_constraint = pyo.Constraint(model.Days, rule=max_workouts_per_day_rule)

    # constraint 1a: no more than 1 workout of each sport per day

    def max_workouts_per_day_by_sport_rule(m,day,sport):
        relevant_workouts = swim_workouts
        match sport:
            case "swim":
                relevant_workouts = swim_workouts
            case "bike":
                relevant_workouts = bike_workouts
            case "run":
                relevant_workouts = run_workouts

        return sum(m.SelectedWorkouts[(day,workout_id)] for workout_id in relevant_workouts) <=1

    model.max_workouts_per_day_by_sport_constraint = pyo.Constraint(model.Days, model.Sports, rule=max_workouts_per_day_by_sport_rule)

    # constraint 2: fatigue must remain below maximum for each sport

    def must_not_exceed_max_fatigue_by_sport_rule(m,day,sport):
        relevant_workouts = swim_workouts
        relevant_incoming_fatigue = incoming_fatigue[sport]
        match sport:
            case "swim":
                relevant_workouts = swim_workouts
            case "bike":
                relevant_workouts = bike_workouts
            case "run":
                relevant_workouts = run_workouts

        if day == 0:
            return relevant_incoming_fatigue + sum(fatigue_increase_dict[workout_id]*m.SelectedWorkouts[(day,workout_id)] for workout_id in relevant_workouts) <= m.FatigueUpperBound
        

        day_range = range(0,day)
        incoming_fagigue_coef = 1-(day*.25)
        if day > 4:
            day_range = range(day-5,day)
            incoming_fagigue_coef = 0


        return incoming_fagigue_coef*relevant_incoming_fatigue + sum(fatigue_increase_dict[workout_id]*m.SelectedWorkouts[(d,workout_id)] for workout_id in relevant_workouts for d in day_range) <= m.FatigueUpperBound

    model.must_not_exceed_max_fatigue_by_sport_constraint = pyo.Constraint(model.Days, model.Sports, rule=must_not_exceed_max_fatigue_by_sport_rule)

    # constraint 2a: total fatigue across sports must remain below maximum

    def must_not_exceed_max_total_fatigue_rule(m,day):
        workout_dict = {
            "swim": swim_workouts,
            "bike": bike_workouts,
            "run": run_workouts
        }

        incoming_fatigue_total = sum(incoming_fatigue[sport] for sport in m.Sports) 
        if day == 0:
            return incoming_fatigue_total + sum(fatigue_increase_dict[workout_id]*m.SelectedWorkouts[(day,workout_id)] for workout_id in m.WorkoutIds) <= m.TotalFatigueUpperBound
        

        day_range = range(0,day)
        incoming_fagigue_coef = 1-(day*.25)
        if day > 4:
            day_range = range(day-5,day)
            incoming_fagigue_coef = 0


        return incoming_fagigue_coef*incoming_fatigue_total + sum(fatigue_increase_dict[workout_id]*m.SelectedWorkouts[(d,workout_id)] for workout_id in m.WorkoutIds for d in day_range) <= m.TotalFatigueUpperBound

    model.must_not_exceed_max_total_fatigue_constraint = pyo.Constraint(model.Days, rule=must_not_exceed_max_total_fatigue_rule)


    # constraint 3: must not exceed weekly duration limit

    def must_not_exceed_weekly_duration_limit_rule(m):

        return sum(duration_dict[workout_id]*m.SelectedWorkouts[(day,workout_id)] for day in m.Days for workout_id in m.WorkoutIds) <= m.WeeklyHoursMax*60

    model.must_not_exceed_weekly_duration_limit_constraint = pyo.Constraint(rule=must_not_exceed_weekly_duration_limit_rule)


    # constraint 4: fitness for sports should not diverge more than X - note: this could become infeasible if the incoming fitness levels at the start are already too far diverged - TODO: account for this

    def must_not_exceed_divergence_limit_rule(m,sport_a,sport_b):
        if sport_a == sport_b:
            return pyo.Constraint.Skip
        sport_a_workouts = []
        match sport_a:
            case "swim":
                sport_a_workouts = swim_workouts
            case "bike":
                sport_a_workouts = bike_workouts
            case "run":
                sport_a_workouts = run_workouts

        sport_b_workouts = []
        match sport_b:
            case "swim":
                sport_b_workouts = swim_workouts
            case "bike":
                sport_b_workouts = bike_workouts
            case "run":
                sport_b_workouts = run_workouts

        return 10 \
            + (incoming_fitness[sport_a]*.95 + sum(model.SelectedWorkouts[(day,workout_id)]*fitness_increase_dict[workout_id]*fitness_multiplier for workout_id in sport_a_workouts for day in model.Days)) \
            - (incoming_fitness[sport_b]*.95 + sum(model.SelectedWorkouts[(day,workout_id)]*fitness_increase_dict[workout_id]*fitness_multiplier for workout_id in sport_b_workouts for day in model.Days)) \
            <= 20 # 10 + x <= 20 on both sides is like abs(x) <= 10

    model.must_not_exceed_divergence_limit_constraint = pyo.Constraint(model.Sports, model.Sports, rule=must_not_exceed_divergence_limit_rule)

    def must_have_variability_in_workouts_rule(m,day,workout_id):
        if day == 0:
            return pyo.Constraint.Skip
        start_day = 0
        if day > 3:
            start_day = day - 3
        day_range = range(start_day,day)

        return sum(model.SelectedWorkouts[(day,workout_id)] for day in day_range) <=1

    model.must_have_variability_in_workouts_constraint = pyo.Constraint(model.Days, model.WorkoutIds, rule=must_have_variability_in_workouts_rule)


    # solve
    solver = pyo.SolverFactory('glpk')
    solver.options['tmlim'] = 10
    results = solver.solve(model)


    
    # print results
    # print(results)
    # model.pprint()
    


    #parse results and add workouts to week
    workouts = []

    for day in model.Days:
        workouts_for_day = []
        for workout_id in model.WorkoutIds:
            if model.SelectedWorkouts[(day,workout_id)].value == 1:
                workouts_for_day.append(available_workouts[workout_id])
        workouts.append(workouts_for_day)

    week["workouts"] = workouts


    def fitness_gain(sport):
        match sport:
            case "swim":
                return sum(model.SelectedWorkouts[(day,workout_id)].value*fitness_increase_dict[workout_id]*fitness_multiplier for workout_id in swim_workouts for day in model.Days)
            case "bike":
                return sum(model.SelectedWorkouts[(day,workout_id)].value*fitness_increase_dict[workout_id]*fitness_multiplier for workout_id in bike_workouts for day in model.Days)
            case "run":
                return sum(model.SelectedWorkouts[(day,workout_id)].value*fitness_increase_dict[workout_id]*fitness_multiplier for workout_id in run_workouts for day in model.Days)

    
    week["fitness_outcome"] = { 
        "run": incoming_fitness["run"]*.95 + fitness_gain("run"), # depreciate a bit of incoming fitness and add on gains
        "bike": incoming_fitness["bike"]*.95 + fitness_gain("bike"),
        "swim": incoming_fitness["swim"]*.95 + fitness_gain("swim")
    }

    
    def fatigue_outcome(sport):
        day_range = range(3,6)
        match sport:
            case "swim":
                return sum(model.SelectedWorkouts[(day,workout_id)].value*fatigue_increase_dict[workout_id] for workout_id in swim_workouts  for day in day_range) 
            case "bike":
                return sum(model.SelectedWorkouts[(day,workout_id)].value*fatigue_increase_dict[workout_id] for workout_id in bike_workouts  for day in day_range)
            case "run":
                return sum(model.SelectedWorkouts[(day,workout_id)].value*fatigue_increase_dict[workout_id] for workout_id in run_workouts  for day in day_range)
    
    week["fatigue_outcome"] = {
        "swim":  fatigue_outcome("swim"),
        "bike": fatigue_outcome("bike"),
        "run": fatigue_outcome("run")
    }

    print(week["fatigue_outcome"])
    
    return week

