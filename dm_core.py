import hashlib, datetime, dm_global, dm_ansi, dm_comm

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
		self.USER_COMMANDS = {

			'bye': (self.bye,
				"%sbye%s - Logs out and exits the server%s",
				dm_global.USER),

			'help': (self.help,
				"%shelp%s - Shows helpful information!%s",
				dm_global.USER),

			'passwd': (self.passwd,
				"%spasswd%s - Changes password%s",
				dm_global.USER),

			'perms': (self.perms,
				"%sperms%s - Shows you what your permissions are%s",
				dm_global.USER),

			'join': (self.join,
				"%sjoin%s - Joins a channel%s",
				dm_global.CHANNEL)

		}
		# Global commands dictionary

		self.GLOBAL_COMMANDS = {

			'welcome_edit': (self.welcome_edit,
				"%swelcome_edit%s - Changes the welcome banner which displays on connect%s",
				dm_global.ADMIN),

			'login_edit': (self.login_edit,
				"%slogin_edit%s - Changes the login banner which displays on login%s",
				dm_global.ADMIN),

			'newuser_edit': (self.newuser_edit,
				"%snewuser_edit%s - Changes the banner which displays on creation of a new account%s",
				dm_global.ADMIN),

			'broadcast': (self.broadcast,
				"%sbroadcast%s - Broadcasts a message%s",
				dm_global.ADMIN),

			'ch_perm': (self.change_permissions,
				"%sch_perm%s - Changes the permissions for a particular user. Format: 'ch_perm <user> <+/-> <permission>'%s",
				dm_global.ADMIN),

			'get_perm': (self.get_permissions,
				"%sget_perm%s - Displays a list of possible permissions%s",
				dm_global.ADMIN),

			'write_helpfile': (self.write_helpfile,
				"%swrite_helpfile%s - Writes a new helpfile for users to read!%s",
				dm_global.MODERATOR),

			'silence': (self.silence,
				"%ssilence%s - Silences a given user. Usage: 'silence <username>'%s",
				dm_global.MODERATOR),

			'unsilence': (self.unsilence,
				"%ssilence%s - Unsilences a given user. Usage: 'unsilence <username>'%s",
				dm_global.MODERATOR),

			'open': (self.open,
				"%sopen%s - Opens a channel with a title. Usage: 'open <title>'%s",
				dm_global.ADMIN),

			'shutdown': (self.shutdown,
				"%sshutdown%s - Shuts down the server%s",
				dm_global.ADMIN)

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
		self.mailbox = dm_comm.Mailbox(self.a_account_name, [self], [])

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
		if command[0] == '@':
			if not self.silenced and command[1:] in dm_comm.MAILBOXES:
				dm_comm.MAILBOXES[command[1:]].recieve_message(args, self.mailbox)
		elif command in self.GLOBAL_COMMANDS and self.has_permission(self.GLOBAL_COMMANDS[command][2]):
			self.client.send(self.GLOBAL_COMMANDS[command][0](args))
			self.client.send(dm_ansi.CLEAR)
		elif command in dm_comm.CHANNELS:
			self.client.send(dm_comm.CHANNELS[command].handle_input(args, self))
		elif command in self.USER_COMMANDS and self.has_permission(self.USER_COMMANDS[command][2]):
			self.client.send(self.USER_COMMANDS[command][0](args))
			self.client.send(dm_ansi.CLEAR)
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
	def hf_title(self, message):
		"""
		Adds a helpfile that users can access by entering the 'help' command followed by the filename.
		Step 1 (and the setup for 2) of the Helpfile sequence
		"""
		if len(message) == 0:
			return
		if message in HELPFILES:
			self.client.send("That file already exists!")
			return
		self.helpfile_title = message
		#Step 2 stuff!
		helpfile_body = MultilineInput(self.hf_submit, self.activate_standardseq)
		self.message_function = helpfile_body.input
		self.client.send("Text:\n(Type 'end' to finish or 'cancel' to cancel)\n")
	def hf_submit(self, fulltext):
		"""
		Finalizes the helpfile and submits it to the database.
		Step 3 of the helpfile sequence
		"""
		dm_global.db_conn.create_helpfile(self.helpfile_title, fulltext)
		self.message_function = self.standardseq_command;
		HELPFILES[self.helpfile_title] = fulltext
		self.helpfile_title = None
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
			helpstring = "List of Commands: \n\n"
			for command in self.GLOBAL_COMMANDS:
				if self.has_permission(self.GLOBAL_COMMANDS[command][2]):
					helpstring += self.GLOBAL_COMMANDS[command][1] % (dm_ansi.CYAN, dm_ansi.GREEN, dm_ansi.CLEAR + "\n")
			for command in self.USER_COMMANDS:
				if self.has_permission(self.USER_COMMANDS[command][2]):
					helpstring += self.USER_COMMANDS[command][1] % (dm_ansi.CYAN, dm_ansi.GREEN, dm_ansi.CLEAR + "\n")
			helpstring += "\n\nList of help files. To read, type in the 'help' command, followed by the name of the file.\nExample: 'help About' reads the 'About' file.:\n\n%s" % (dm_ansi.YELLOW)
			for hfile in HELPFILES:
				helpstring += hfile
			helpstring += "\n"
			return helpstring
		elif args in HELPFILES:
			return HELPFILES[args]
		elif args in self.GLOBAL_COMMANDS:
			return self.GLOBAL_COMMANDS[args][1] % (dm_ansi.CYAN, dm_ansi.GREEN, dm_ansi.CLEAR + "\n")
		else:
			return "Helpfile '%s' not found. Try help on its own to see a list of helpfiles and commands" % (args)
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
	def join(self, args):
		"""
		Joins a channel
		"""
		if args in dm_comm.CHANNELS:
			if not dm_comm.CHANNELS[args].private:
				return dm_comm.CHANNELS[args].plug(self)
		else:
			return "Channel does not exist!"
	#
	# GLOBAL COMMANDS - commands that have to do with server-wide actions or admin level stuff
	#
	def silence(self, args):
		"""
		Command to shut off user access to all channels.
		"""
		if len(args) == 0:
			return;
		for user in dm_global.USER_LIST:
			if user.a_account_name == args:
				user.a_silenced = True
				dm_global.db_conn.update_user_silence(user)
				return "Muted"
			return "That user doesn't exist!"
	def unsilence(self, args):
		"""
		Command to turn on user access to channels.
		"""
		if len(args) == 0:
			return;
		for user in dm_global.USER_LIST:
			if user.a_account_name == args:
				user.a_silenced = False
				dm_global.db_conn.update_user_silence(user)
				return "Unmuted"
			return "That user doesn't exist!"
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

	def welcome_edit(self, args):
		"""
		Changes the welcome (on connect) banner
		"""
		self.client.send("Enter the new banner text:\n(Type 'end' to finish or 'cancel' to cancel)\n")
		mli = MultilineInput(self.welcome_edit_write, self.activate_standardseq)
		self.message_function = mli.input

	def welcome_edit_write(self, text):
		dm_global.db_conn.write_welcome_banner(text)
		self.message_function = self.standardseq_command
		dm_global.WELCOME_MESSAGE = text
	def login_edit(self, args):
		"""
		Changes the login banner
		"""
		self.client.send("Enter the new banner text:\n(Type 'end' to finish or 'cancel' to cancel)\n")
		mli = MultilineInput(self.login_edit_write, self.activate_standardseq)
		self.message_function = mli.input
	def login_edit_write(self, text):
		dm_global.db_conn.write_login_banner(text)
		self.message_function = self.standardseq_command
		dm_global.LOGIN_MESSAGE = text
	def newuser_edit(self, args):
		"""
		Changes the new user banner
		"""
		self.client.send("Enter the new banner text:\n(Type 'end' to finish or 'cancel' to cancel)\n")
		mli = MultilineInput(self.newuser_edit_write, self.activate_standardseq)
		self.message_function = mli.input
	def newuser_edit_write(self, text):
		dm_global.db_conn.write_newuser_banner(text)
		self.message_function = self.standardseq_command
		dm_global.NEW_USER_MESSAGE = text
	def open(self, args):
		"""
		Open a channel
		"""
		if args == "":
			self.client.send("Please enter in the name of the channel you would like to open. Format 'open <name>'\n")
		else:
			if len(args) > 128:
				self.client.send("Channel name too long. Must be < 128 characters\n")
				return
			if args in self.GLOBAL_COMMANDS or args in self.USER_COMMANDS:
				self.client.send("Channel name cannot conflict with an existing command\n")
			if args in dm_comm.CHANNELS:
				self.client.send("Channel already exists with that name\n")
				return
			dm_comm.Channel(args)
			dm_global.db_conn.create_channel(args)
			self.client.send("Channel '%s%s%s' created\n" % (dm_ansi.CYAN, args, dm_ansi.CLEAR))
			return
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
			return "Too few arguments. Be sure to use the format 'ch_perm <user> <+/-> <permission>'"
		elif arg_list[1] not in ("+", "-"):
			return "Invalid argument. Be sure to use the format 'ch_perm <user> <+/-> <permission>'"
		elif arg_list[2] not in dm_global.PERMS_DICT:
			return "Invalid permissions. Use the get_perm command to view all valid permission types."
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
	def shutdown(self, args):
		"""
		Shutdown
		"""
		self.broadcast("SYSTEM IS SHUTTING DOWN NOW!")
		raise dm_global.ExitSignal(0)
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
		self.mailbox = None
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
	#
	#
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
	#
	# Takes two function names as input. The function to call with the full data, and a function to call when quitting
	#
	def __init__(self, callback, cancel):
		self.callback = callback
		self.text = ""
		self.cancel = cancel

	def input(self, message):
		"""
		Method to add input
		"""
		if len(message) == 0:
			self.text += "\n"
		elif message == "end":
			self.callback(self.text)
		elif message == "cancel":
			self.cancel()
		else:
			self.text += str(message)
			self.text += "\n"