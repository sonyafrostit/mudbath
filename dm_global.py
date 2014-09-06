import dm_db, dm_comm
# Database Connection
db_conn = dm_db.DatabaseConnection(username='mudbath', password='St1ll@l1v3!', database='mudbath')

# List of online users
USER_LIST = []

# Salt for the password table to protect against rainbow table attacks
SALT = db_conn.execute_query("SELECT salt FROM serverdata;")[0][0]


# Timeout for idle clients
TIMEOUT = db_conn.execute_query("SELECT timeout FROM serverdata;")[0][0]

# Welcome message: On Connect
WELCOME_MESSAGE = db_conn.execute_query("SELECT welcome FROM serverdata;")[0][0]

# Login Message: On Login
LOGIN_MESSAGE = db_conn.execute_query("SELECT login FROM serverdata;")[0][0]

NEW_USER_MESSAGE = db_conn.execute_query("SELECT newuser FROM serverdata;")[0][0]
# Helpfiles
HELPFILES = db_conn.get_helpfiles()


# Commends dictionary
COMMANDS = {}


#Reserved Words: Words you cannot use for channel names!

RESERVED_WORDS = []
def reserve_word(word):
	if word not in RESERVED_WORDS:
		RESERVED_WORDS.add(word)

def unreserve_word(word):
	if word in RESERVED_WORDS:
		RESERVED_WORDS.remove(word)

def is_reserved(word):
	return word in RESERVED_WORDS

#
# Function to clean up data when user goes offline
#

def cleanup(user_addrport):
	for user in USER_LIST:
		if user.client.addrport() == user_addrport:
			USER_LIST.remove(user)
			user.client = None
			for channel in dm_comm.CHANNELS:
				dm_comm.CHANNELS[channel].unplug_user(user)
			return
			
# Permission Groups
#
# How it works: Addition and subtraction. If you want to add a person to a group, add the group to their a_permissions. As in, a_permissions += group. Subtract for taking away permissions.
# 
# To check for permissions, use modulus. (I.E, if someone is ROOT, then a_permissions % 2 > 0, if ADMIN, then a_permissions % 4 > 1, if MODERATOR then a_permissions % 8 > 3 ) For an implementation, look at User.has_permission()
#

# ROOT: All commands, trump card. DONT USE THIS PERMISSION!
ROOT = 1
# ADMIN: Commands that have to do with the server
ADMIN = 2 
# MODERATOR: Commands that have to do with ability to moderate the game and issue bans/lower-level permissions. Chat channels
MODERATOR = 4

USER = 8

CHANNEL = 16

# For use when parsing commands only. Use the previous groups to add permissons
PERMS_DICT = {

	"Admin" : ADMIN,

	"Mod" : MODERATOR,

	"User" : USER, # Avoid removing this permission! It prevents you from even logging out!

	"Chan" : CHANNEL,

}

DEFAULT_PERMISSIONS = USER + CHANNEL
dm_comm.load_channels()
# Load channels

class ExitSignal(Exception):
	def __init__(user, value):
		user.value = value
	def __str__(user):
		return repr(user.value)

# COMMANDS SECTION!
#
# GLOBAL COMMANDS - commands that have to do with server-wide actions or admin level stuff
#
def silence(user, args):
	"""
	Command to shut off user access to all channels.
	"""
	if len(args) == 0:
		return;
	for user in USER_LIST:
		if user.a_account_name == args:
			user.a_silenced = True
			db_conn.update_user_silence(user)
			return "Muted"
		return "That user doesn't exist!"
def unsilence(user, args):
	"""
	Command to turn on user access to channels.
	"""
	if len(args) == 0:
		return;
	for user in USER_LIST:
		if user.a_account_name == args:
			user.a_silenced = False
			db_conn.update_user_silence(user)
			return "Unmuted"
		return "That user doesn't exist!"
def broadcast(user, args):
	"""
	Send msg to every client.
	"""
	for user in USER_LIST:
		if user.logged_in:
			user.client.send(args)
	return ""
def write_helpfile(user, args):
	"""
	Start create helpfile sequence
	"""
	user.message_function = user.hf_title
	user.client.send("Title: ")

def welcome_edit(user, args):
	"""
	Changes the welcome (on connect) banner
	"""
	user.client.send("Enter the new banner text:\n(Type 'end' to finish or 'cancel' to cancel)\n")
	mli = MultilineInput(user.welcome_edit_write, user.activate_standardseq)
	user.message_function = mli.input

def welcome_edit_write(user, text):
	db_conn.write_welcome_banner(text)
	user.message_function = user.standardseq_command
	WELCOME_MESSAGE = text
def login_edit(user, args):
	"""
	Changes the login banner
	"""
	user.client.send("Enter the new banner text:\n(Type 'end' to finish or 'cancel' to cancel)\n")
	mli = MultilineInput(user.login_edit_write, user.activate_standardseq)
	user.message_function = mli.input
def login_edit_write(user, text):
	db_conn.write_login_banner(text)
	user.message_function = user.standardseq_command
	LOGIN_MESSAGE = text
def newuser_edit(user, args):
	"""
	Changes the new user banner
	"""
	user.client.send("Enter the new banner text:\n(Type 'end' to finish or 'cancel' to cancel)\n")
	mli = MultilineInput(user.newuser_edit_write, user.activate_standardseq)
	user.message_function = mli.input
def newuser_edit_write(user, text):
	db_conn.write_newuser_banner(text)
	user.message_function = user.standardseq_command
	NEW_USER_MESSAGE = text
def open(user, args):
	"""
	Open a channel
	"""
	if args == "":
		user.client.send("Please enter in the name of the channel you would like to open. Format 'open <name>'\n")
	else:
		if len(args) > 128:
			user.client.send("Channel name too long. Must be < 128 characters\n")
			return
		if is_reserved(args):
			user.client.send("Channel name cannot conflict with an existing command or channel!\n")
			return
		dm_comm.Channel(args)
		db_conn.create_channel(args)
		user.client.send("Channel '%s%s%s' created\n" % (dm_ansi.CYAN, args, dm_ansi.CLEAR))
		return
# NOTE: These commands are for administrators. Moderators can only silence/unsilence.
# They can also shadowban.
# Even administrators should use these commands instead when dealing with rogue users,
# because they send alerts to user inboxes. (Or they will when implemented)
# These should be used to make users mods or admins
def change_permissions(user, args):
	"""
	Change the permissions of a particular user. Args in the format of <user> <+/-> <permission>
	"""
	arg_list = args.lstrip().split(' ')
	if len(arg_list) < 3:
		return "Too few arguments. Be sure to use the format 'ch_perm <user> <+/-> <permission>'"
	elif arg_list[1] not in ("+", "-"):
		return "Invalid argument. Be sure to use the format 'ch_perm <user> <+/-> <permission>'"
	elif arg_list[2] not in PERMS_DICT:
		return "Invalid permissions. Use the get_perm command to view all valid permission types."
	else:
		if arg_list[1] == "-":
			return db_conn.change_permissions_cmd(arg_list[0], -1 * PERMS_DICT[arg_list[2]])
		else:
			return db_conn.change_permissions_cmd(arg_list[0], PERMS_DICT[arg_list[2]])

def get_permissions(user, args):
	"""
	Displays a list of permissions groups
	"""
	s = ""
	for key in PERMS_DICT.keys():
		s += "%s\n"%(key)
	return s
def shutdown(user, args):
	"""
	Shutdown
	"""
	user.broadcast("SYSTEM IS SHUTTING DOWN NOW!")
	raise ExitSignal(0)
#
# HELPFILE SEQUENCE
#
# 1. Get the title. Do not accept blank input
# 2. Get the text of the file using a MultilineInput
# 3. Submit it to the database when the user puts in "end"
#
def hf_title(user, message):
	"""
	Adds a helpfile that users can access by entering the 'help' command followed by the filename.
	Step 1 (and the setup for 2) of the Helpfile sequence
	"""
	if len(message) == 0:
		return
	if message in HELPFILES:
		user.client.send("That file already exists!")
		return
	user.helpfile_title = message
	#Step 2 stuff!
	helpfile_body = MultilineInput(user.hf_submit, user.activate_standardseq)
	user.message_function = helpfile_body.input
	user.client.send("Text:\n(Type 'end' to finish or 'cancel' to cancel)\n")
def hf_submit(user, fulltext):
	"""
	Finalizes the helpfile and submits it to the database.
	Step 3 of the helpfile sequence
	"""
	db_conn.create_helpfile(user.helpfile_title, fulltext)
	user.message_function = user.standardseq_command;
	HELPFILES[user.helpfile_title] = fulltext
	user.helpfile_title = None
# Global commands dictionary

GLOBAL_COMMANDS = {
	'welcome_edit': (welcome_edit,
		"%swelcome_edit%s - Changes the welcome banner which displays on connect%s",
		ADMIN),
	'login_edit': (login_edit,
		"%slogin_edit%s - Changes the login banner which displays on login%s",
		ADMIN),

	'newuser_edit': (newuser_edit,
		"%snewuser_edit%s - Changes the banner which displays on creation of a new account%s",
		ADMIN),

	'broadcast': (broadcast,
		"%sbroadcast%s - Broadcasts a message%s",
		ADMIN),

	'ch_perm': (change_permissions,
		"%sch_perm%s - Changes the permissions for a particular user. Format: 'ch_perm <user> <+/-> permission>'%s",
		ADMIN),

	'get_perm': (get_permissions,
		"%sget_perm%s - Displays a list of possible permissions%s",
		ADMIN),

	'write_helpfile': (write_helpfile,
		"%swrite_helpfile%s - Writes a new helpfile for users to read!%s",
		MODERATOR),

	'silence': (silence,
		"%ssilence%s - Silences a given user. Usage: 'silence <username>'%s",
		MODERATOR),

	'unsilence': (unsilence,
		"%ssilence%s - Unsilences a given user. Usage: 'unsilence <username>'%s",
		MODERATOR),

	'open': (open,
		"%sopen%s - Opens a channel with a title. Usage: 'open <title>'%s",
		ADMIN),

	'shutdown': (shutdown,
		"%sshutdown%s - Shuts down the server%s",
		ADMIN)

}

def help(user, args):
	"""
	Displays the help string for each command
	"""
	if args == "":
		helpstring = "List of Commands: \n\n"
		for command in COMMANDS:
			if user.has_permission(COMMANDS[command][2]):
				helpstring += COMMANDS[command][1] % (dm_ansi.CYAN, dm_ansi.GREEN, dm_ansi.CLEAR + "\n")
		helpstring += "\n\nList of help files. To read, type in the 'help' command, followed by the name of the file.\nExample: 'help About' reads the 'About' file.:\n\n%s" % (dm_ansi.YELLOW)
		for hfile in HELPFILES:
			helpstring += hfile
		helpstring += "\n"
		return helpstring
	elif args in HELPFILES:
		return HELPFILES[args]
	elif args in COMMANDS:
		return COMMANDS[args][1] % (dm_ansi.CYAN, dm_ansi.GREEN, dm_ansi.CLEAR + "\n")
	else:
		return "Helpfile '%s' not found. Try help on its own to see a list of helpfiles and commands" % (args)
def bye(user, args):
	"""
	Deactivates the client for pickup by the main server loop
	"""
	user.client.deactivate()
def passwd(user, args):
	"""
	Changes the user password. Starts the "Change Password" Sequence
	"""
	user.activate_chpass()
def perms(user, args):
	"""
	Displays a list of permissions that the user has
	"""
	if user.a_permissions == ROOT:
		user.client.send("Root")
	else:
		for key in PERMS_DICT:
			if user.has_permission(.PERMS_DICT[key]):
				user.client.send(key + "\n")
def join(user, args):
	"""
	Joins a channel
	"""
	if args in dm_comm.CHANNELS:
		if not dm_comm.CHANNELS[args].private:
			return dm_comm.CHANNELS[args].plug(user)
	else:
		return "Channel does not exist!"


# User Commands!

user.USER_COMMANDS = {

	'bye': (bye,
		"%sbye%s - Logs out and exits the server%s",
		USER),

	'help': (help,
		"%shelp%s - Shows helpful information!%s",
		USER),

	'passwd': (passwd,
		"%spasswd%s - Changes password%s",
		USER),

	'perms': (perms,
		"%sperms%s - Shows you what your permissionsare%s",
		USER),

	'join': (join,
		"%sjoin%s - Joins a channel%s",
		CHANNEL)

}

COMMANDS.update(GLOBAL_COMMANDS)
COMMANDS.update(USER_COMMANDS)
	
	
#
# MultilineInput - A unique class to add multiline input over telnet.
#

class MultilineInput:
	#
	# Takes two function names as input. The function to call with the full data, and a function to call when quitting
	#
	def __init__(user, callback, cancel):
		user.callback = callback
		user.text = ""
		user.cancel = cancel

	def input(user, message):
		"""
		Method to add input
		"""
		if len(message) == 0:
			user.text += "\n"
		elif message == "end":
			user.callback(user.text)
		elif message == "cancel":
			user.cancel()
		else:
			user.text += str(message)
			user.text += "\n"
			
