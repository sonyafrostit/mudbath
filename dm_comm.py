class Channel:
	
	
	def __init__(self, c_name, co_connections=[], c_active=True):
		self.c_name = c_name # All c_ variables correspond to values in the channels table. co refers to connections table
		self.co_connections = co_connections
		
