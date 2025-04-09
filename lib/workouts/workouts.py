import csv

workout_path = './workout_library/workouts_test.csv'
cached_workouts = []

def fetch_workouts_with_cache():
	if len(cached_workouts) > 0:
		return cached_workouts
	else:
		with open(workout_path, 'r') as file: 
			workout_csv_reader = csv.reader(file)
			line_num = 0
			for row in workout_csv_reader:
				# possible improvement: use headers to generate dictionary

				if line_num != 0:
					print(row)
					# parse row and add workout to library
					new_workout = {
						"sport": row[0],
						"workout_name": row[1],
						"intensity": float(row[2]),
						"duration": float(row[3]),
						"fatigue_increase": float(row[4]),
						"fitness_increase": float(row[5]),
						"week_blocks": row[6]
					}
					cached_workouts.append(new_workout)

				line_num += 1

		return cached_workouts

def strategy_matches(week_strategy):
	def filter_function(workout):
		# filter out if strategy string is found in block string
		return not (week_strategy in workout["week_blocks"])
	return filter_function

def GetWorkoutsForWeek(week_strategy):
	all_workouts = fetch_workouts_with_cache()
	
	# filter by week strategy 
	filtered_workouts = list(filter(strategy_matches(week_strategy), all_workouts))

	return filtered_workouts
