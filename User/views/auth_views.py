from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    
    return render(request,'index.html')

def signup(request):
    return render(request,'signup.html')
