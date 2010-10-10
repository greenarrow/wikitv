import re, datetime, BeautifulSoup
from django.db import models
from django.contrib.auth.models import User


def extractDate(string):
	"""Attempts to extract date form sting in various formats"""
	
	try:
		date = datetime.datetime.strptime(string, "%d %B %Y").date()
	except ValueError:
		pass
	else:
		return date
	try:
		date = datetime.datetime.strptime(string, "%B %d, %Y").date()
	except ValueError:
		pass
	else:
		return date
	
	raise ParseError


class ParseError(Exception):
	"""Something went wrong while parsing"""
	pass


class Show(models.Model):
	"""A show that a user can subscribe to"""
	title = models.CharField(max_length=255)

	def __unicode__(self):
		if self.title == None:
			return u"NULL"
		else:
			return self.title


class Episode(models.Model):
	"""A single episode from a show"""
	title = models.CharField(max_length=255, blank=True, null=True)
	show = models.ForeignKey(Show, blank=True, null=True)
	series = models.IntegerField(blank=True, null=True)
	series_index = models.IntegerField(blank=True, null=True)
	show_index = models.IntegerField(blank=True, null=True)
	date_broadcast = models.DateField(blank=True, null=True)
	date_found = models.DateField(blank=True, null=True)

	def __unicode__(self):
		if self.title == None:
			return u"NULL"
		else:
			return u"%s: S%d.E%d - %s" % (self.show.title, self.series, self.series_index, self.title)

	def fromHTML(self, headers, html):
		soup = BeautifulSoup.BeautifulSoup(html)
		columns = soup.findAll("td")
		
		# Check we have all the titles we need for reference
		if len( filter( lambda h: h not in headers, ["#", "Title","Original air date"] ) ):
			print headers
			raise ParseError
		
		# Determine whether show_index is being used
		if headers[1] == "#":
			self.show_index = int( columns[0].string )
			self.series_index = int( columns[1].string )
		else:
			self.series_index = self.show_index = int( columns[0].string )

		self.title = ( columns[ headers.index("Title") ].find( "a", title=re.compile(r'\D+') ) or columns[ headers.index("Title") ].find("b") ).string

		if self.title == None:
			raise ParseError

		for item in columns[ headers.index("Original air date") ].contents:
			try:
				self.date_broadcast = extractDate( str(item) )
			except ParseError:
				continue
			else:
				break

		if self.date_broadcast == None:
			for span in columns[ headers.index("Original air date") ].findAll("span"):
				try:
					self.date_broadcast = extractDate(span.string)
				except ParseError:
					continue
				else:
					break

		if self.date_broadcast == None:
			print "# NO DATE #"
			#print html

	def prettyDate(self):
		return self.date_broadcase.strftime("%d %B %Y")

	def save(self):
		if not self.id:
			self.date_found = datetime.date.today()
		super(Episode, self).save()

	class Meta:
		ordering = ["series", "series_index"]


class Subscription(models.Model):
	"""The shows that a user has subscribed to"""
	user = models.ForeignKey(User)
	shows = models.ManyToManyField(Show)

	def __unicode__(self):
		return self.user.username


