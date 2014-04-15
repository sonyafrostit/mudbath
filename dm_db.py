import MySQLdb as mdb
import datetime, sys

class DatabaseConnection:

	def __init__(self, username, database, password=None):
		try:
			# Start a connection to a local database, entering in a password if necessary
			if password is None:
				self.conn = mdb.connect(host='localhost', user=username, db=database)
			else:
				self.conn = mdb.connect(host='localhost', user=username, db=database, passwd=password)
		except mdb.Error, e:
  			print "Error %d: %s" % (e.args[0],e.args[1])
			sys.exit(1)

	def execute_query(self, query, params=None):
		"""
		A function that returns the results of a query from the database
		Precondition: The connection must be initialized
		"""
		cursor = self.conn.cursor()
		if params is None:
			cursor.execute(query)
		else:
			cursor.execute(query, params)
		return cursor.fetchall()
	# Helpfiles stuff
	def get_helpfiles(self):
		query_results = self.execute_query("SELECT name, fullfile FROM helpfiles;")
		helpfiles_dict = {}
		for helpfile in query_results:
			helpfiles_dict[helpfile[0]] = helpfile[1]
		return helpfiles_dict
		

	# Account management
	def get_user_info(self, username):
		"""
		A function that gets all the data associated with a username in the database. Used for logins
		Precondition: The connection must be initialized
		"""
		query_results = self.execute_query("SELECT account_id, creation_date, display_name, password, last_visit_date, permissions FROM accounts WHERE account_name = %s", [username])
		if len(query_results) > 0:
			return query_results[0]
		else:
			return None

	
	def write_new_user(self, user):
		"""
		Takes a dm_core User object as input and writes it to the database, returning the values for autogens in a tuple.
		"""
		self.execute_query("INSERT INTO accounts(account_name, password, permissions) VALUES(%s, %s, %s);", [user.a_account_name, user.a_password, user.a_permissions])
		self.conn.commit()
		return self.execute_query("SELECT account_id, creation_date FROM accounts WHERE account_name = %s;", [user.a_account_name]) # Get autogens and return them
	def update_login_date(self, a_account_id):
		"""
		Updates the column that shows the last date logged in with account.
		"""
		self.execute_query("UPDATE accounts SET last_visit_date=%s WHERE account_id=%s;", [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), a_account_id])
		self.conn.commit()

	
	def check_for_username(self, username):
		"""
		Checks for duplicates of a username. Returns true if the username doesn't exist in the database, false if it does.
		"""
		return len(self.execute_query("SELECT * FROM accounts WHERE account_name = %s;", [username])) == 0
	def change_account_id_attribute(self, attribute, value, a_account_id):
		"""
		Changes attribute for given account id to value in database. exitDO NOT take "attribute" as raw user input.
		"""
		self.execute_query("UPDATE accounts SET {a}=%s WHERE account_id=%s;".format(a=attribute), [value, a_account_id])
		self.conn.commit()
	def change_account_attribute(self, attribute, value, a_account_name):
		"""
		Changes attribute for given account name to value in database. DO NOT take "attribute" as raw user input.
		"""
		self.execute_query("UPDATE accounts SET {a}=%s WHERE account_name=%s;".format(a=attribute), [value, a_account_name])
		self.conn.commit()
	def change_permissions_cmd(self, account_name, perm_change):
		"""
		Does data checks before changing permissions. perm_change is a number. Positive for adding permissions, negative for removing them"
		"""
		if account_name == "root":
			return "Cannot add or remove permissions to root user!"
		q_res = self.execute_query("SELECT permissions FROM accounts WHERE account_name=%s;", [account_name])
		if len(q_res) > 0:
			if q_res[0][0] % (abs(perm_change) * 2) >= abs(perm_change):
				if perm_change > 0:
					return "That user is already has those permissions!"
				else:
					self.change_account_attribute("permissions", "%s"%(q_res[0][0] + perm_change), account_name)
					return "Removed Permissions"
			else:
				if perm_change < 0:
					return "That user doesn't have those permissions!"
				else:
					self.change_account_attribute("permissions", "%s"%(q_res[0][0] + perm_change), account_name)
					return "Added Permissions"
		else:
			return "That user doesn't exist!"

	# Channels data

	def create_channel(self, c_name, owner_co_account_id):
		self.execute_query("INSERT INTO channels (name, active) VALUES (%s, true);", [c_name])
		self.conn.commit()
		self.execute_query("INSERT INTO channel_connections (account_id, conn_role, active, channel_id) VALUES ( %s, 0, true, %s);", [owner_co_account_id, self.conn.insert_id()])
		self.conn.commit()
