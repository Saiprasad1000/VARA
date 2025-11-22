from .common_importers import *
# Create your views here.

def admin_home(request):
    return render(request,'admin_home.html')

def sales_report(request):
    return render(request,'sales_report.html')


def products(request):
    return render(request,'products.html')
def coupoen(request):
    return render(request,'coupen.html')
def banner_management(request):
    return render(request,'offers.html')
def banner_management(request):
    return render(request,'offers.html')

