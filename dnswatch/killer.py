import signal
<<<<<<< HEAD
import logging

class Killer:
    kill_now = False
    reload_now = False

    def __init__(self):
        self.logger = logging.getLogger("DNSWatch.Killer()")

        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        signal.signal(signal.SIGHUP, self.reload_app)
        signal.signal(signal.SIGUSR1, self.exit_wo_cleanup)

    def exit_gracefully(self, signum, frame):
	self.logger.debug("Signal handler called with signal: {}.".format(signum))
        self.kill_now = True
        self.cleanup = True

    def reload_app(self, signum, frame):
	self.logger.debug("Signal handler called with signal: {}.".format(signum))
        self.reload_now = True

    def exit_wo_cleanup(self, signum, frame):
	self.logger.debug("Signal handler called with signal: {}.".format(signum))
        self.kill_now = True
        self.cleanup = False
=======

class Killer:
    kill_now = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self,signum, frame):
        self.kill_now = True
>>>>>>> 59ed5eec90df781060c3439a5ca2940dcdb5fdb9
