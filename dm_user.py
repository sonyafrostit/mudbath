import hashlib, datetime, dm_global, dm_ansi, dm_permissions

#
# dm_global.HELPFILES - A way to create some helpfiles for the benefit of users! Hopefully they'll read 'em....hopefully
#



#
# User Class - Used to connect server to user
#
class User:


	def __init__(self, client):
		
		self.client = client # Our TCP/Telnet Client
		self.client.send(dm_global.WELCOME_MESSAGE + "\n")
		# Begin Login Sequence:
		client.send("Username (if this is your first visit, enter in a username to sign up): ")
		self.message_function = self.login_uname
		
		self.password_attempts = 0
		self.silenced = False
		# To prevent function calls when data has not yet been populated as necessary for preconditions
		self.logged_in = False 
		# functions to handle user input
		# User Commands. Moderator commands, account commands, and one-to-one messaging commands.
		
		

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
			return
		# Populate Account Data
		# ALL variables beginning with "a_" correspond to a database column in the "accounts" table
		self.a_account_id = user_data[0]
		self.a_creation_date = user_data[1]
		self.a_display_name = user_data[2]
		self.a_password = user_data[3]
		self.a_last_visit_date = user_data[4]
		self.a_permissions = user_data[5] # See how pretty and efficient this is? :D
		self.a_silenced = user_data[6]
		

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

			self.client.send(dm_global.LOGIN_MESSAGE + "\n")
			self.logged_in = True
			self.client.send("Last Visit was on %s\n"%(self.a_last_visit_date))
			dm_global.db_conn.update_login_date(self.a_account_id)
			self.message_function = self.standardseq_command
			self.password_attempts = 0
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
			self.newaccount_username(self.a_account_name)
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
			self.client.send("You entered in username '%s'. Is this OK? (Yes/No) "%(self.a_account_name))
	def newaccount_username(self, message):
		"""
		Get a username. Step 3 of New Account Sequence
		"""
		if len(message) == 0:
			return
		self.a_account_name = message
		if len(self.a_account_name) > 128:
			self.client.send("You entered username '%s', however that is too long. Please enter in a username that is less than 128 characters long: ")
			return
		if self.a_account_name.find(' ') > -1:
			self.client.send("You entered username '%s', however that has spaces in it. Please enter in a username that has no spaces: ")
			return
		if dm_global.db_conn.check_for_username(self.a_account_name):
			self.message_function = self.newaccount_usernameconfirm;
			self.client.send("You entered in username '%s'. Is this OK? (Yes/No) "%(self.a_account_name))
		else:
			self.message_function = self.newaccount_username
			self.client.send("That username is already taken. Please enter a new one: ")
	def newaccount_password(self, message):
		"""
		Get a password. Step 4 of New Account Sequence
		"""
		if len(message) == 0:
			self.client.send("You cannot have a blank password. Please try again: ")
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
			self.client.send(dm_global.NEW_USER_MESSAGE)
			self.client.send("\n\n>>")
			self.message_function = self.standardseq_command
			
		else:
			self.client.send("Passwords do not match!\n")
			
			self.message_function = self.newaccount_password
			self.client.send("Enter a Password (Warning: This will be sent over insecure connection): ")

	# STANDARD SEQUENCE
	#
	# Take user input and match it with all commands
	# Be sure to check command permissions.
	def activate_standardseq(self):
		self.message_function = self.standardseq_command
	def standardseq_command(self, message):
		if len(message) == 0:
			return
		if message.find(' ') > -1:
			command = message[:message.find(' ')]
			args = message[message.find(' ') + 1:]
		else:
			command = message
			args = ""
		if command in dm_global.COMMANDS and self.has_permission(dm_global.COMMANDS[command][2]):
			self.client.send(dm_global.COMMANDS[command][0](self, args))
			self.client.send(dm_ansi.CLEAR)
		elif command in dm_global.dm_comm.CHANNELS:
			self.client.send(dm_global.dm_comm.CHANNELS[command].handle_input(args, self))
		else:
			self.client.send("Command/Channel either does not exist or you do not have permission to do that. Try 'help' if you're lost!\n")
			# We don't show if you don't have permissions or if its a typo. We just remove all access.

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
			dm_global.db_conn.change_password(self, self.new_pass)
			self.a_password = self.new_pass
			self.new_pass = None
			self.message_function = self.standardseq_command
		else:
			self.client.send("Passwords do not match!\nNew Password:")
			self.message_function = self.chpass_new_prompt
	
	# USER COMMANDS
	#
	# These are for use by everyone. They're even left on for people who are banned,
	# although the 'silenced' flag may disable some of them.
	#
	
	
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
		self.a_last_visit_date = None
		self.a_permissions = None # See how pretty and efficient this is? :D
		self.a_silenced = None
		
		# Login Message
		self.client.send("Username (if this is your first visit, enter in a username to sign up): ")
		self.logged_in = False # To prevent function calls when data has not yet been populated as necessary for preconditions
		# Login Sequence
		self.message_function = self.login_uname
	
	def __eq__(self, other):
        	return (isinstance(other, self.__class__)
            	and self.client == other.client) # Users are the same if their clients are the same.
        										 # Keep in mind a user is NOT the same as an account.

    	def __ne__(self, other):
        	return not self.__eq__(other)
