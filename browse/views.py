from django.shortcuts import render_to_response
import backend.models as models

def index(request):
	shows = models.Show.objects.all()
	return render_to_response( "browse/index.html", {"shows":shows} )
