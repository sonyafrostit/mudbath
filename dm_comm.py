import dm_global, dm_ansi

class Channel:
	def __init__(self, name, topic=""):
		self.name = name
		self.topic = topic
		self.users = []
		self.hushed_users = []
		self.gagged_users = []
		self.banned_users = []
	def unplug_user(self, user):
		"""
		Unplug a user from the channel.
		"""
		if user in self.users:
			self.users.remove(user)
			self.broadcast("%sUser %s disconnected%s from %s" % (dm_ansi.RED, account_name, self.name, dm_ansi.CLEAR)
			return (True, "User successfully disconnected from channel")
		else:
			return (False, "User not connected to channel"
	def broadcast(self, message):
		"""
		Send a message to everyone!
		"""
		for user in self.users:
			user.client.send(message)
		return (True, "Message broadcast successfully")
	def hush(self, user):
		"""
		Hush user so they can still see messages but not send them. 
		"""
		if user in self.hushed_users:
			return (False, "User already hushed")
		else:
			self.hushed_users.add(user)
			return (True, "User hushed")
	def plug_user(self, user):
		"""
		Plug a user into the channel
		"""
		if user in self.banned_users:
			return (False, "User is banned")
		elif user in self.users:
			return (False, "User already in channel")
		else:
			self.users.add(user)
			return (False, "User added to channel")
			
	def gag(self, user):
		"""
		Gag is like shadowban
		"""
		self.gagged_users.add(user)
	def ban(self, user):
		"""
		BAN HAMMER!
		"""
		if user in users:
			self.unplug_user(user)
		if user in self.banned_users:
			return (False, "User already banned")
		else:
			self.banned_users.add(user)
			(True, "User added to banlist")
	def msg(self, message, user):
		"""
		Called when a user sends a message
		"""
		if user not in users:
			return (False, "You're not connected to that channel!")
		elif user in hushed_users:
			return (False, "You're not able to send messages to that channel!")
		elif user in gagged_users:
			return (False, self.format_message(message, user)) # Gagged user can't see that they're banned.
		else:
			self.broadcast(self.format_message(message, user))
			return (True, "")

