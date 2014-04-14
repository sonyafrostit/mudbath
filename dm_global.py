import dm_db

# Database Connection
db_conn = dm_db.DatabaseConnection(username='mudbath', password='St1ll@l1v3!', database='mudbath')

# List of online users
USER_LIST = []

# Salt for the password table to protect against rainbow table attacks
SALT = db_conn.execute_query("SELECT salt FROM serverdata;")[0][0]
# Timeout for idle clients
TIMEOUT = db_conn.execute_query("SELECT timeout FROM serverdata;")[0][0]
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

# For use when parsing commands only. Use the previous groups to programattically add permissons
PERMS_DICT = {
"Admin" : ADMIN,
"Mod" : MODERATOR,
"User" : USER, # Avoid removing this permission! It prevents you from even logging out!
"Chan" : CHANNEL,
}

DEFAULT_PERMISSIONS = USER + CHANNEL
