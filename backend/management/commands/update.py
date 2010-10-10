import urllib2, BeautifulSoup, re, datetime, smtplib
from email.mime.text import MIMEText
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
import backend.models as models



def readManifest(show):
	data = urllib2.urlopen( urllib2.Request( "http://en.wikipedia.org/wiki/List_of_%s_episodes" % show.title.replace(" ", "_"), headers={"User-Agent":settings.USER_AGENT} ) ).read()
	soup = BeautifulSoup.BeautifulSoup(data)
	manifest = []

	for series in soup("h3"):
		table = series.findNextSibling("table")
		r = re.findall( r'Series (\d+)', str(series) ) + re.findall( r'Season (\d+)', str(series) )
		if len(r):
			index = int( r[0] )
		else:
			print "skipping", series
			continue

		headers = [ h.string for h in table.find("tr").findAll("th") ]

		for row in table.findAll( "tr", **{"class":"vevent"} ):
			episode = models.Episode(show=show, series=index)

			#try:
			episode.fromHTML( headers, str(row) )
			if episode.date_broadcast == None:
				print "Malformed row (probably incomplete)"
			else:
				manifest.append(episode)

	return manifest


class Command(BaseCommand):
	args = '<poll_id poll_id ...>'
	help = 'Closes the specified poll for voting'

	def handle(self, *args, **options):
		new_episodes = {}
		# Grab the current Wikipedia eisode manifest for every show
		for show in models.Show.objects.all():
			print "fetch manifest for show %s" % show.title
			episodes = readManifest(show)
			# Save any new episodes to the database
			new = filter( lambda e: len( models.Episode.objects.filter(show=show, show_index=e.show_index) ) == 0, episodes )
			for e in new:
				e.save()

			if len(new):
				new_episodes[show] = new
				print "  %d new episodes" % len(new)

		if len(new_episodes) == 0:
			return

		# Connect to the SMTP server
		smtpserver = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
		smtpserver.ehlo()
		smtpserver.starttls()
		smtpserver.ehlo()
		smtpserver.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

		# Send a mail to every subscriber with new listings on shows
		for subscription in models.Subscription.objects.filter(shows=show):
			body = "<h2>New Episodes Listed</h2>\n"
			for show, episodes in new_episodes.iteritems():
				# todo use template
				#for e in episodes:
				#	print e.series, e.series_index, e.title
				#	print type(e.series), type(e.series_index), type(e.title)
				body += "<h3>%s</h3>\n<ul>%s</ul>\n" % ( show.title, "\n".join( [ "<li>S%d.E%d - %s</li>" % (e.series, e.series_index, e.title) for e in episodes ] ) )
			print "send to %s" % subscription.user.email
			print body

			msg = MIMEText(body, "html")
			msg["Subject"] = "WikiTV Notification"
			msg["To"] = subscription.user.email
			msg["From"] = settings.SMTP_USER
			smtpserver.sendmail( settings.SMTP_USER, subscription.user.email, msg.as_string() )

		smtpserver.quit()


