import dm_global, dm_ansi

class Channel:
	def __init__(self, name, topic="", active=True):
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
			self.broadcast("%sUser %s disconnected%s from %s" % (dm_ansi.RED, account_name, self.name, dm_ansi.CLEAR))
			return "User successfully disconnected from channel"
		else:
			return "User not connected to channel"
	def broadcast(self, message, exceptions=[]):
		"""
		Send a message to everyone!
		"""
		for user in self.users:
			if user not in exceptions:
				user.client.send(message)
		return "Message broadcast successfully"
	def hush(self, user):
		"""
		Hush user so they can still see messages but not send them. 
		"""
		if user in self.hushed_users:
			return "User already hushed"
		else:
			self.hushed_users.add(user)
			return "User hushed"
	def plug(self, user):
		"""
		Plug a user into the channel
		"""
		if user in self.banned_users:
			return "User is banned"
		elif user in self.users:
			return "User already in channel"
		else:
			self.users.add(user)
			return "User added to channel"
			
	def gag(self, user):
		"""
		Gag is like shadowban
		"""
		if user in self.gagged_users:
			return "User is already gagged!"
		else:
			self.gagged_users.add(user)
			return "Gagged"

	def ban(self, user):
		"""
		BAN HAMMER!
		"""
		if user in users:
			self.unplug_user(user)
		if user in self.banned_users:
			return "User already banned"
		else:
			self.banned_users.add(user)
			return "User added to banlist"
	def msg(self, message, user):
		"""
		Called when a user sends a message
		"""
		if user not in users:
			return "You're not connected to that channel!"
		elif user in hushed_users:
			return "You're not able to send messages to that channel!"
		elif user in gagged_users:
			return self.format_message(message, user) # Gagged user can't see that they're banned.
		elif user.silenced:
			return "You have been silenced. Please contact an admin."
		else:
			return ""

