# Permission Groups
#
# How it works: Addition and subtraction. If you want to add a person to a group, add the group to their a_permissions. As in, a_permissions += group. Subtract for taking away permissions.
# 
# To check for permissions, use modulus. (I.E, if someone is ROOT, then a_permissions % 2 > 0, if ADMIN, then a_permissions % 4 > 1, if MODERATOR then a_permissions % 8 > 3 ) For an implementation, look at has_permission()
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

def has_permission(self, perm_group):
"""
Checks to see if user is has perm_group permissions
"""
return self.a_permissions == dm_global.ROOT or self.a_permissions % (perm_group * 2) > perm_group - 1 # Oh yeah, it's that easy.
	