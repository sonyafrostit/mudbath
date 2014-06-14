#!/usr/bin/env python
import dm_global, dm_core, traceback
from miniboa import TelnetServer

SERVER_RUN = True


def on_connect(client):
    """
    Sample on_connect function.
    Handles new connections.
    """
    print "++ Opened connection to %s" % client.addrport()
    
    dm_global.USER_LIST.append(dm_core.User(client))
    


def on_disconnect(client):
	"""
	Handles lost connections.
	"""
	print "-- Lost connection to %s" % client.addrport()
	dm_global.cleanup(user.client.addrport())



def kick_idle():
    """
    Looks for idle clients and disconnects them by setting active to False.
    """
    if dm_global.TIMEOUT == 0:
        return
    ## Who hasn't been typing?
    for user in dm_global.USER_LIST:
        if user.client.idle() > dm_global.TIMEOUT:
            print('-- Kicking idle lobby client from %s' % user.client.addrport())
            user.client.deactivate


def process_clients():
    """
    Check each client, if client.cmd_ready == True then there is a line of
    input available via client.get_command().
    """
    global SERVER_RUN
    for user in dm_global.USER_LIST:
        try:
            if user.client.active and user.client.cmd_ready:
                ## If the client sends input echo it to the chat room
                chat(user)
        except dm_global.ExitSignal as ex:
            print "Bye!"
            SERVER_RUN = False
        except:
            user.client.send(traceback.format_exc())
            traceback.print_exc()

    


def chat(user):
    """
    Echo whatever client types to everyone.
    """
    global SERVER_RUN
    msg = user.client.get_command()
    user.message_function(msg)


#------------------------------------------------------------------------------
#       Main
#------------------------------------------------------------------------------

if __name__ == '__main__':

    ## Simple chat server to demonstrate connection handling via the
    ## async and telnet modules.

    ## Create a telnet server with a port, address,
    ## a function to call with new connections
    ## and one to call with lost connections.

    telnet_server = TelnetServer(
        port=7777,
        address='',
        on_connect=on_connect,
        on_disconnect=on_disconnect,
        timeout = .05
        )

    print(">> Listening for connections on port %d.  CTRL-C to break."
        % telnet_server.port)

    ## Server Loop
    while SERVER_RUN:
        telnet_server.poll()        ## Send, Recv, and look for new connections
        kick_idle()                 ## Check for idle clients
        process_clients()           ## Check for client input

    print(">> Server shutdown.")
