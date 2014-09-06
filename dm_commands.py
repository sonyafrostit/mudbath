import dm_global



#
# GLOBAL COMMANDS - commands that have to do with server-wide actions or admin level stuff
#
def silence(user, args):
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
def unsilence(user, args):
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
def broadcast(user, args):
	"""
	Send msg to every client.
	"""
	for user in dm_global.USER_LIST:
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
	dm_global.db_conn.write_welcome_banner(text)
	user.message_function = user.standardseq_command
	dm_global.WELCOME_MESSAGE = text
def login_edit(user, args):
	"""
	Changes the login banner
	"""
	user.client.send("Enter the new banner text:\n(Type 'end' to finish or 'cancel' to cancel)\n")
	mli = MultilineInput(user.login_edit_write, user.activate_standardseq)
	user.message_function = mli.input
def login_edit_write(user, text):
	dm_global.db_conn.write_login_banner(text)
	user.message_function = user.standardseq_command
	dm_global.LOGIN_MESSAGE = text
def newuser_edit(user, args):
	"""
	Changes the new user banner
	"""
	user.client.send("Enter the new banner text:\n(Type 'end' to finish or 'cancel' to cancel)\n")
	mli = MultilineInput(user.newuser_edit_write, user.activate_standardseq)
	user.message_function = mli.input
def newuser_edit_write(user, text):
	dm_global.db_conn.write_newuser_banner(text)
	user.message_function = user.standardseq_command
	dm_global.NEW_USER_MESSAGE = text
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
		if dm_global.is_reserved(args):
			user.client.send("Channel name cannot conflict with an existing command or channel!\n")
			return
		dm_comm.Channel(args)
		dm_global.db_conn.create_channel(args)
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
	elif arg_list[2] not in dm_global.PERMS_DICT:
		return "Invalid permissions. Use the get_perm command to view all valid permission types."
	else:
		if arg_list[1] == "-":
			return dm_global.db_conn.change_permissions_cmd(arg_list[0], -1 * dm_global.PERMS_DICT[arg_list[2]])
		else:
			return dm_global.db_conn.change_permissions_cmd(arg_list[0], dm_global.PERMS_DICT[arg_list[2]])

def get_permissions(user, args):
	"""
	Displays a list of permissions groups
	"""
	s = ""
	for key in dm_global.PERMS_DICT.keys():
		s += "%s\n"%(key)
	return s
def shutdown(user, args):
	"""
	Shutdown
	"""
	user.broadcast("SYSTEM IS SHUTTING DOWN NOW!")
	raise dm_global.ExitSignal(0)
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
		user.client.send("That file already exists!")
		return
	user.helpfile_title = message
	#Step 2 stuff!
	helpfile_body = MultilineInput(user.hf_submit, user.activate_standardseq)
	user.message_function = helpfile_body.input
	user.client.send("Text:\n(Type 'end' to finish or 'cancel' to cancel)\n")
def hf_submit(self, fulltext):
	"""
	Finalizes the helpfile and submits it to the database.
	Step 3 of the helpfile sequence
	"""
	dm_global.db_conn.create_helpfile(user.helpfile_title, fulltext)
	user.message_function = user.standardseq_command;
	HELPFILES[user.helpfile_title] = fulltext
	user.helpfile_title = None
# Global commands dictionary

GLOBAL_COMMANDS = {
	'welcome_edit': (welcome_edit,
		"%swelcome_edit%s - Changes the welcome banner which displays on connect%s",
		dm_global.ADMIN),
	'login_edit': (login_edit,
		"%slogin_edit%s - Changes the login banner which displays on login%s",
		dm_global.ADMIN),

	'newuser_edit': (newuser_edit,
		"%snewuser_edit%s - Changes the banner which displays on creation of a new account%s",
		dm_global.ADMIN),

	'broadcast': (broadcast,
		"%sbroadcast%s - Broadcasts a message%s",
		dm_global.ADMIN),

	'ch_perm': (change_permissions,
		"%sch_perm%s - Changes the permissions for a particular user. Format: 'ch_perm <user> <+/-> permission>'%s",
		dm_global.ADMIN),

	'get_perm': (get_permissions,
		"%sget_perm%s - Displays a list of possible permissions%s",
		dm_global.ADMIN),

	'write_helpfile': (write_helpfile,
		"%swrite_helpfile%s - Writes a new helpfile for users to read!%s",
		dm_global.MODERATOR),

	'silence': (silence,
		"%ssilence%s - Silences a given user. Usage: 'silence <username>'%s",
		dm_global.MODERATOR),

	'unsilence': (unsilence,
		"%ssilence%s - Unsilences a given user. Usage: 'unsilence <username>'%s",
		dm_global.MODERATOR),

	'open': (open,
		"%sopen%s - Opens a channel with a title. Usage: 'open <title>'%s",
		dm_global.ADMIN),

	'shutdown': (shutdown,
		"%sshutdown%s - Shuts down the server%s",
		dm_global.ADMIN)

}
#
# User Commands!
#


	
	
	
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
			
# Add commands to master list
dm_global.COMMANDS.update(GLOBAL_COMMANDS)