from django.shortcuts import render

# Create your views here.

def home(request):
    data = 'hello x2'
    return render(request, 'app/home.html', {
        'data': data
    })
