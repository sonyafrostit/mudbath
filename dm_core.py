import hashlib, datetime, dm_global

#
# HELPFILES - A way to create some helpfiles for the benefit of users! Hopefully they'll read 'em....hopefully
#

HELPFILES = dm_global.db_conn.get_helpfiles()

#
# User Class - Used to connect server to user
#
class User:


	def __init__(self, client):
		self.client = client # Our TCP/Telnet Client
		# Begin Login Sequence:
		client.send("Username (if this is your first visit, enter in a username to sign up): ")
		self.message_function = self.login_uname
		self.silenced = False
		self.password_attempts = 0

		# To prevent function calls when data has not yet been populated as necessary for preconditions
		self.logged_in = False 
		# functions to handle user input
		# User Commands. Moderator commands, account commands, and one-to-one messaging commands.
		self.USER_COMMANDS = {

			'bye': (self.bye,
				"/bye - Logs out and exits the server",
				dm_global.USER),

			'help': (self.help,
				"/help - Shows helpful information!",
				dm_global.USER),

			'passwd': (self.passwd,
				"/passwd - Changes password",
				dm_global.USER),

			'perms': (self.perms,
				"/perms - Shows you what your permissions are",
				dm_global.USER)

		}
		# Global commands dictionary

		self.GLOBAL_COMMANDS = {

			'broadcast': (self.broadcast,
				"/broadcast - Broadcasts a message",
				dm_global.ADMIN),

			'ch_perm': (self.change_permissions,
				"/ch_perm - Changes the permissions for a particular user. Format: '/ch_perm <user> <+/-> <permission>'",
				dm_global.ADMIN),

			'get_perm': (self.get_permissions,
				"/get_perm - Displays a list of possible permissions",
				dm_global.ADMIN),

			'write_helpfile': (self.write_helpfile,
				"/write_helpfile - Writes a new helpfile for users to read!",
				dm_global.MODERATOR)

		}
	# LOGIN SEQUENCE
	#
	# 1. Get Username input from user and look up in database.
	#    If there is no user with that username, go to New Account Sequence (login_uname)
	# 2. Get Password input from user, hash it against database entry.
	#    Go to Standard Sequence if correct. Revert to Step 1 if incorrect.
	#

	def login_uname(self, message):
		"""
		Used to get username input from end user. Start of Login Sequence.
		"""
		if len(message) == 0:
			return
		# Corresponds to database entry, but this one is special because we need it to get the rest of the data.
		# Also, the New Account Sequence needs a value for the username
		self.a_account_name = message
		user_data = dm_global.db_conn.get_user_info(message) # Query database for user info
		if user_data is None:
			# Go to New Account Sequence
			self.activate_newaccount()
		
		# Populate Account Data
		# ALL variables beginning with "a_" correspond to a database column in the "accounts" table
		self.a_account_id = user_data[0]
		self.a_creation_date = user_data[1]
		self.a_display_name = user_data[2]
		self.a_password = user_data[3]
		self.a_last_visit_date = user_data[4]
		self.a_permissions = user_data[5] # See how pretty and efficient this is? :D
		# Continue Login Sequence
		self.message_function = self.login_passwd
		self.client.send("Password:")


	def login_passwd(self, message):
		"""
		Used to get and validate user input for the password. Part 2 of Login Sequence
		"""
		self.password_attempts += 1

		if len(message) == 0:
			return
		if hashlib.sha256(message + dm_global.SALT).hexdigest() == self.a_password:
			# TODO Implement Standard Sequence
			self.client.send("Welcome!\n\n")
			self.logged_in = True
			self.client.send("Last Visit was on %s\n"%(self.a_last_visit_date))
			dm_global.db_conn.update_login_date(self.a_account_id)
			self.message_function = self.standardseq_command
			self.password_attempts = 0
			self.client.send("\n>>")
		else:
			if self.password_attempts == 5:
				self.client.send("Too many attempts. Disconnecting.")
				self.client.deactivate()
			else:
				self.client.send("Incorrect Password. Please Try Again\n")
				self.logout()


	# NEW ACCOUNT SEQUENCE
	#
	# 1. Confirm that they actually want to create a new account, or if they just misspelled their account name (newaccount_confirm)
	# 2. Confirm their username, go to step 3 if they don't like the current one.
	#    If they like it, go to step 4 (newaccount_usernameconfirm)
	# 3. Get a new username and check to see if it's unique. If so, go to step 2. If not, repeat.
	# 4. Get a password
	# 5. Confirm that password. If it didn't work, go back to step 4.
	#    If it did, write their info into the database, log them in, and go to Standard Sequence
	#
	def activate_newaccount(self):
		"""
		Activate method for new account sequence.
		"""
		self.client.send("User '%s' doesn't exist, would you like to create a new account? (Yes/No)" % self.a_account_name)
		self.message_function = self.newaccount_confirm
		return
	def newaccount_confirm(self, message):
		"""
		Confirm user wants to make a new account. Beginning point of New Account Sequence
		"""
		if len(message) == 0:
			return
		if message.upper()[0] == 'Y': # Only check the first letter, because it covers the most cases.
			self.message_function = self.newaccount_usernameconfirm;
			self.client.send("You entered in username %s. Is this OK? (Yes/No)"%(self.a_account_name))
		elif message.upper()[0] == 'N':
			
			self.logout()
		# If they give us garbage, just repeat. No harm done
		else:
			self.client.send("User '%s' doesn't exist, would you like to create a new account? (Yes/No)" % message)

	def newaccount_usernameconfirm(self, message):
		"""
		Confirm that the username is good with the user. Step 2 of New Account Sequence
		"""
		if len(message) == 0:
			return
		if message.upper()[0] == 'Y':
			self.message_function = self.newaccount_password;
			self.client.send("Enter a Password (Warning: This will be sent over insecure connection): ")
		elif message.upper()[0] == 'N':
			self.message_function = self.newaccount_username
			self.client.send("Enter a Username: ")
		else:
			self.client.send("You entered in username %s. Is this OK? (Yes/No) "%(self.a_account_name))
	def newaccount_username(self, message):
		"""
		Get a username. Step 3 of New Account Sequence
		"""
		if len(message) == 0:
			return
		self.a_account_name = message
		if dm_global.db_conn.check_for_username(self.a_account_name):
			self.message_function = self.newaccount_usernameconfirm;
			self.client.send("You entered in username %s. Is this OK? (Yes/No) "%(self.a_account_name))
		else:
			self.message_function = self.newaccount_username
			self.client.send("That username is already taken. Please enter a new one: ")
	def newaccount_password(self, message):
		"""
		Get a password. Step 4 of New Account Sequence
		"""
		if len(message) == 0:
			return
		self.a_password = hashlib.sha256(message + dm_global.SALT).hexdigest()
		self.message_function = self.newaccount_passwordconfirm;
		self.client.send("Confirm Password: ")
	def newaccount_passwordconfirm(self, message):
		"""
		Confirm password and finish. Step 5 of New Account Sequence
		"""
		if len(message) == 0:
			return
		if hashlib.sha256(message + dm_global.SALT).hexdigest() == self.a_password:

			self.a_permissions = dm_global.DEFAULT_PERMISSIONS

			# Write to database and get the creation date and id
			autogens = dm_global.db_conn.write_new_user(self) 
			self.a_account_id = autogens[0]
			self.a_creation_date = autogens[1]
			self.logged_in = True
			self.client.send("Welcome!")
			self.message_function = self.standardseq_command
			
		else:
			self.client.send("Passwords do not match!\n")
			
			self.message_function = newaccount_password
			self.client.send("Enter a Password (Warning: This will be sent over insecure connection): ")

	# STANDARD SEQUENCE
	#
	# Take user input and match it with all commands
	# Be sure to check command permissions.

	def standardseq_command(self, message):
		if len(message) == 0:
			return
		if message[0] == '/':
			command = ""
			if len(message) == 1:
				return
			if message.find(' ') > -1:
				command = message[1:message.find(' ')]
				args = message[message.find(' ') + 1:]
			else:
				command = message[1:]
				args = ""
			if command in self.GLOBAL_COMMANDS and self.has_permission(self.GLOBAL_COMMANDS[command][2]):
				self.client.send(self.GLOBAL_COMMANDS[command][0](args))
			elif command in self.USER_COMMANDS and self.has_permission(self.USER_COMMANDS[command][2]):
				self.client.send(self.USER_COMMANDS[command][0](args))
			else:	
				self.client.send("Command either does not exist or you do not have permission to do that. Try '/help' if you're lost!\n")
				# We don't show if you don't have permissions or if its a typo. We just remove all access.
		else:
			self.client.send(message)
		if self.message_function == self.standardseq_command:
			self.client.send("\n>>")

	# CHANGE PASSWORD SEQUENCE
	#
	# 1. Prompt user for the old password. If the user inputs the correct password, then proceed to step 2. 
	#    If the user doesn't, prompt them 4 more times and exit to standard sequence.
	# 2. Prompt the user for a new password. Accept all non-blank input. Continue to step 3
	# 3. Prompt the user to confirm their password. If they don't match, go back to step 2. 
	#    If they do match, change the password and then go back to standard sequence.

	def activate_chpass(self):
		self.client.send("Old password:")
		self.message_function = self.chpass_old_prompt
	def chpass_old_prompt(self, message):
		"""
		Entry point for Change password sequence. Prompts user for their password.
		"""
		if len(message) == 0:
			return
		self.password_attempts += 1
		if hashlib.sha256(message + dm_global.SALT).hexdigest() == self.a_password:
			self.message_function = self.chpass_new_prompt
			self.client.send("New Password: ")
			self.password_attempts = 0
		else:
			if self.password_attempts == 5:
				self.message_function = self.standardseq_command
				self.client.send("Too many attempts, quitting")
			else:
				self.client.send("Incorrect password")
	def chpass_new_prompt(self, message):
		"""
		Step 2 of Change password sequence. Prompts for a new password.
		"""
		if len(message) == 0:
			return
		self.new_pass = hashlib.sha256(message + dm_global.SALT).hexdigest() 
		self.client.send("Confirm password: ")
		self.message_function = self.chpass_new_confirm
	def chpass_new_confirm(self, message):
		"""
		Step 3 of change password sequence. Prompts to confirm password.
		"""
		if len(message) == 0:
			return
		if self.new_pass == hashlib.sha256(message + dm_global.SALT).hexdigest():
			dm_global.db_conn.change_account_id_attribute("password", self.new_pass, self.a_account_id)
			self.a_password = self.new_pass
			self.new_pass = None
			self.message_function = self.standardseq_command
		else:
			self.client.send("Passwords do not match!\nNew Password:")
			self.message_function = self.chpass_new_prompt
	#
	# HELPFILE SEQUENCE
	#
	# 1. Get the title. Do not accept blank input
	# 2. Get the text of the file using a MultilineInput
	# 3. Submit it to the database when the user puts in "end"
	#
	def hf_title(self, args):
		"""
		Adds a helpfile that users can access by entering the 'help' command followed by the filename.
		Step 1 (and the setup for 2) of the Helpfile sequence
		"""
		if len(args) == 0:
			return
		self.helpfile_title = args
		#Step 2 stuff!
		helpfile_body = MultilineInput(self.hf_submit)
		self.message_function = helpfile_body.input
		self.client.send("Text (type 'end' on its own line to end input): ")
	def hf_submit(self, fulltext):
		"""
		Finalizes the helpfile and submits it to the database.
		Step 3 of the helpfile sequence
		"""
		dm_global.db_conn.create_helpfile(self.helpfile_title, fulltext)
		self.message_function = self.standardseq_command;
		self.HELPFILES[helpfile_title] = fulltext
		self.helpfile_title = None

		self.client.send(">>")
	# USER COMMANDS
	#
	# These are for use by everyone. They're even left on for people who are banned,
	# although the 'silenced' flag may disable some of them.
	#
	def help(self, args):
		"""
		Displays the help string for each command
		"""
		if args == "":
			helpstring = ""
			for command in self.GLOBAL_COMMANDS:
				if self.has_permission(self.GLOBAL_COMMANDS[command][2]):
					helpstring += self.GLOBAL_COMMANDS[command][1] + '\n'
			for command in self.USER_COMMANDS:
				if self.has_permission(self.USER_COMMANDS[command][2]):
					helpstring += self.USER_COMMANDS[command][1] + '\n'
			for hfile in HELPFILES:
				helpstring += hfile
			return helpstring
		elif args in HELPFILES:
			return HELPFILES[args]
		elif args in self.GLOBAL_COMMANDS:
			return self.GLOBAL_COMMANDS[args][1]
		else:
			return "Helpfile %s not found. Try /help on its own to see a list of helpfiles and commands" % (args)
	def bye(self, args):
		"""
		Deactivates the client for pickup by the main server loop
		"""
		self.client.deactivate()
	def passwd(self, args):
		"""
		Changes the user password. Starts the "Change Password" Sequence
		"""
		self.activate_chpass()
	def perms(self, args):
		"""
		Displays a list of permissions that the user has
		"""
		if self.a_permissions == dm_global.ROOT:
			self.client.send("Root")
		else:
			for key in dm_global.PERMS_DICT:
				if self.has_permission(dm_global.PERMS_DICT[key]):
					self.client.send(key + "\n")
	#
	# GLOBAL COMMANDS - commands that have to do with server-wide actions or admin level stuff
	#

	def broadcast(self, args):
		"""
		Send msg to every client.
		"""
		for user in dm_global.USER_LIST:
			if user.logged_in:
				user.client.send(args)
		return ""
	def write_helpfile(self, args):
		"""
		Start create helpfile sequence
		"""
		self.message_function = self.hf_title
		self.client.send("Title: ")
	# NOTE: These commands are for administrators. Moderators can only silence/unsilence.
	# They can also shadowban.
	# Even administrators should use these commands instead when dealing with rogue users,
	# because they send alerts to user inboxes. (Or they will when implemented)
	# These should be used to make users mods or admins
	def change_permissions(self, args):
		"""
		Change the permissions of a particular user. Args in the format of <user> <+/-> <permission>
		"""
		arg_list = args.lstrip().split(' ')
		if len(arg_list) < 3:
			return "Too few arguments. Be sure to use the format '/ch_perm <user> <+/-> <permission>'"
		elif arg_list[1] not in ("+", "-"):
			return "Invalid argument. Be sure to use the format '/ch_perm <user> <+/-> <permission>'"
		elif arg_list[2] not in dm_global.PERMS_DICT:
			return "Invalid permissions. Use the /get_perm command to view all valid permission types."
		else:
			if arg_list[1] == "-":
				return dm_global.db_conn.change_permissions_cmd(arg_list[0], -1 * dm_global.PERMS_DICT[arg_list[2]])
			else:
				return dm_global.db_conn.change_permissions_cmd(arg_list[0], dm_global.PERMS_DICT[arg_list[2]])

	def get_permissions(self, args):
		"""
		Displays a list of permissions groups
		"""
		s = ""
		for key in dm_global.PERMS_DICT.keys():
			s += "%s\n"%(key)
		return s
	
	#
	# Other misc methods
	#
	def logout(self):
		"""
		Used to logout the user or to reset data in New Account and Login Sequences
		"""
		# Depopulate account data from database.
		self.a_account_id = None
		self.a_account_name = None
		self.a_creation_date = None
		self.a_display_name = None
		self.a_password = None
		# Login Message
		self.client.send("Username (if this is your first visit, enter in a username to sign up): ")
		self.logged_in = False # To prevent function calls when data has not yet been populated as necessary for preconditions
		# Login Sequence
		self.message_function = self.login_uname
	def has_permission(self, perm_group):
		"""
		Checks to see if user is has perm_group permissions
		"""
		return self.a_permissions == dm_global.ROOT or self.a_permissions % (perm_group * 2) > perm_group - 1 # Oh yeah, it's that easy.

	def __eq__(self, other):
        	return (isinstance(other, self.__class__)
            	and self.client == other.client) # Users are the same if their clients are the same.
        										 # Keep in mind a user is NOT the same as an account.

    	def __ne__(self, other):
        	return not self.__eq__(other)
#
# MultilineInput - A unique class to add multiline input over telnet.
#

class MultilineInput:

	def __init__(self, callback):
		self.callback = callback
		self.text = ""

	def input(self, message):
		"""
		Method to add input
		"""
		if len(message) == 0:
			self.text += "\n"
		elif message == "end":
			self.callback(self.text)
		else:
			self.text += str(message)
			self.text += "\n"