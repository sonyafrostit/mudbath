#
# THE GAME CODE! Where the majicks happen!
#
# This part of the application differs from implementation to implementation, but here is an example of a social MUD system

START_BANNER = "All attributes can be changed after character creation.\n Contact an admin if you don't see the gender or race you want, we might be able to work something out.\n\nWhat is your character's name?"

# What you want to happen when the 
def game_start(user):
	user.client.send(START_BANNER)
	user.game_data = GameData()
	user.message_function = name_function
	
def name_function(user, message):
	user.game_data.name = message
	user.client.send("What is your character's gender? (M/F): ")
	
def gender_function(user, message):
	if message.upper()[0] == "M":
		user.game_data.gender = "Male"
		user.game_data.pos_pn = "his"
		user.game_data.sub_pn = "him"
		user.game_data.obj_pn = "he"
		user.client.send("About how old is your character?")
	elif message.upper()[0] == "F":
		user.game_data.gender = "Female"
		user.game_data.pos_pn = "her"
		user.game_data.sub_pn = "she"
		user.game_data.obj_pn = "her"
		user.client.send("About how old is your character?")
	else:
		user.client.send("Invalid selection. If you don't see the gender or race you want, just select one for now and contact an admin after you're done setting everything else up")
	
def age_function(user, message):
	try:
		char_age = int(message)
		if char_age <=0:
			raise ValueError("Number too small")
		user.game_data.age = char_age
	except ValueError as ex:
		user.client.send("Invalid selection. Please enter a number greater than 0")

def race_function(user, message):
	
class GameData(object):
	pass
	