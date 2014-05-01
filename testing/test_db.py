# A mock class to simulate the dm_db module.
import DateTime

accounts = [
(1, 1, DateTime.DateTime.now(), "root", "832faf612053e6798a05c4aee8cecac7df34a70d804d9e1364c840ad4249b0bc", None, DateTime.DateTime.now(), False),
(2, 30, DateTime.DateTime.now(), "Sonya", "832faf612053e6798a05c4aee8cecac7df34a70d804d9e1364c840ad4249b0bc", None, DateTime.DateTime.now(), False)
]
account_attributes = [a_account_id, a_permissions, a_]
next_account = 3
channels = [
("ooc", 1, 0)
]
helpfiles = [("Willow", "She is evil!")]
serverdata = [("c60bfbdb676892081c2d6cb662756226", 0, "Hello, and welcome to the test server!", "Welcome!","Come on in!")]
channelmessages = []
messages = []
next_message = 0
class DatabaseConnection:

	def __init__(self, username, database, password=None):
		pass


	# Write login and welcome banners
	def write_login_banner(self, text):
		self.serverdata[0][2] = text
	def write_welcome_banner(self, text):
		self.serverdata[0][3] = text
	def write_newuser_banner(self, text):
		self.serverdata[0][4] = text
	# Helpfiles stuff
	def get_helpfiles(self):
		"""
		Pulls helpfiles from the database
		"""
		helpfiles_dict = {}
		for helpfile in helpfiles:
			helpfiles_dict[helpfile[0]] = helpfile[1]
		return helpfiles_dict
	def create_helpfile(self, title, helpfile_text):
		"""
		Creates a new helpfile
		"""
		self.helpfiles.append([title, helpfile_text])
	# Account management
	def get_user_info(self, username):
		"""
		A function that gets all the data associated with a username in the database. Used for logins
		Precondition: The connection must be initialized
		"""
		#self.execute_query("SELECT account_id, creation_date, display_name, password, last_visit_date, permissions, silenced FROM accounts WHERE account_name = %s", [username])
		query_results = []
		for account in accounts:
			if account[3] == username:
				query_results.append((account[0], account[2], account[5], account[4], account[6], account[1], account[7]))
		if len(query_results) > 0:
			return query_results[0]
		else:
			return None

	def update_user_silence(self, user):
		for account in accounts:
			if account[3] == user.a_account_name:
				account[7] = user.silenced

	def write_new_user(self, user):
		"""
		Takes a dm_core User object as input and writes it to the database, returning the values for autogens in a tuple.
		"""
		accounts.append((next_account, user.a_permissions, user.a_account_name, user.a_password, None, DateTime.DateTime.now(), False))
		autogens = (next_account, DateTime.DateTime.now() )
		next_account += 1
		return autogens
	def update_login_date(self, a_account_id):
		"""
		Updates the column that shows the last date logged in with account.
		"""
		for account in accounts:
			if account[0] == a_account_id:
				account[6] = DateTime.DateTime.now())

	
	def check_for_username(self, username):
		"""
		Checks for duplicates of a username. Returns true if the username doesn't exist in the database, false if it does.
		"""
		for account in accounts:
			if account[3] == username:
				return False
		return True
	def change_password(self, user, password):
		for account in accounts:
			if account[3] == user.a_account_name:
				account[4] = password
	def change_permissions_cmd(self, account_name, perm_change):
		"""
		Does data checks before changing permissions. perm_change is a number. Positive for adding permissions, negative for removing them"
		"""
		if account_name == "root":
			return "Cannot add or remove permissions to root user!"
		q_res = []
		for account in accounts:
			if account.a_account_name == account_name:
				q_res.append(account.a_permissions)
		if len(q_res) > 0:
			if q_res[0][0] % (abs(perm_change) * 2) >= abs(perm_change):
				if perm_change > 0:
					return "That user is already has those permissions!"
				else:
					for account in accounts:
						if account.a_account_name == account_name:
							account[1] = q_res[0][0] + perm_change
					return "Removed Permissions"
			else:
				if perm_change < 0:
					return "That user doesn't have those permissions!"
				else:
					for account in accounts:
						if account.a_account_name == account_name:
							account[1] = q_res[0][0] + perm_change
					return "Added Permissions"
		else:
			return "That user doesn't exist!"
	def log_message(self, sender, recipient, message):
		messages.append((next_message, sender, recipient, message, DateTime.DateTime.now()))
	def log_channel(self, sender, channel, message):
		channelmessages.append((sender, channel, message))
		self.conn.commit()
	# Channels data

	def create_channel(self, name):
		channels.append((name, True, False))

	def get_channels():
		return channels


