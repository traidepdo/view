from django.shortcuts import render

# Create your views here.


def home(request):
    data = "hello emiu "
    return render(request, "app/home.html", {"data": data})
