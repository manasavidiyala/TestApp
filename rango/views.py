from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from rango.models import Category, Page
from rango.forms import CategoryForm, PageForm
from rango.forms import UserForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rango.google_search import run_query
from django.shortcuts import redirect

def index(request):
    category_list= Category.objects.order_by('-likes')[:5]
    page_list= Page.objects.order_by('-views')[:5]
    context_dict = {'categories': category_list, 'pages':page_list}
        
    return render(request, 'rango/index.html', context_dict)
	
def about(request):
	context_dict = {'boldmessage': "Rango About page"}
	return render(request, 'rango/about.html', context_dict)

def category(request, category_name_url):
	 # Create a context dictionary which we can pass to the template rendering engine.
    context_dict = {}

    try:
        category = Category.objects.get(slug=category_name_url)
        context_dict['category_name'] = category.name

        # Retrieve all of the associated pages.
        # Note that filter returns >= 1 model instance.
        pages = Page.objects.filter(category=category).order_by('-views')

        # Adds our results list to the template context under name pages.
        context_dict['pages'] = pages
        # We also add the category object from the database to the context dictionary.
        # We'll use this in the template to verify that the category exists.
        context_dict['category'] = category
        likes=category.likes
        context_dict['likes'] = likes
		 
    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything - the template displays the "no category" message for us.
        pass

    # Go render the response and return it to the client.
    return render(request, 'rango/category.html', context_dict)
def add_category(request):
	form = CategoryForm({})
	if request.method == 'POST':
		form = CategoryForm(request.POST)
		if form.is_valid():
			#form.save()
			form.save(commit=True)
			print "saved"
			#return HttpResponse("Rango says Hello World! <a href='/rango/index'>About</a>" )
			return index(request)
		else:
			print form.errors
	else:
		form=CategoryForm()
		#return index(request)
	return render(request, 'rango/add_category.html', {'form': form})

def add_page(request, category_name_slug):
	form = PageForm({})
	print category_name_slug
	try:
		cat = Category.objects.get(slug=category_name_slug)
	except Category.DoesNotExist:
		cat = None
	if request.method == 'POST':
		form = PageForm(request.POST)
        if form.is_valid():
			print "sssssssssssssssssss"
			if cat:
				print "hello Page"
				page = form.save(commit=False)
				page.category = cat
				page.views = 0
				page.save()
                # probably better to use a redirect here.
				return category(request, category_name_slug)
			print form.errors
	else:
		form = PageForm()
	context_dict = {'form':form, 'category': cat}
	return render(request, 'rango/add_page.html', context_dict)

	
def register(request):
	registered = False
	if request.method == 'POST':
		user_form=UserForm(data=request.POST)
		profile_form=UserProfileForm(data=request.POST)
		if user_form.is_valid() and profile_form.is_valid():
			user=user_form.save();
			user.set_password(user.password)
			user.save()
			profile=profile_form.save(commit=False)
			profile.user=user
			if 'picture' in request.FILIES:
				profile.picture=request.FILIES['picture']
			profile.save()
			registered=True
		else:
			print user_form.errors, profile_form.errors
	else:
		user_form=UserForm()
		profile_form=UserProfileForm()
	context_dict={'user_form':user_form, 'profile_form':profile_form}
	return render(request, "rango/register.html", context_dict)
	
def user_login(request):
	if request.method == 'POST':
		username=request.POST.get('username')
		password=request.POST.get('password')
		user=authenticate(username=username,password=password)
		if user:
			if user.is_active:
				login(request,user)
				return HttpResponseRedirect('/rango/')
			else:
				return HttpResponse("User account is disabled")
		else:
			print "Invalid login details: {0}, {1}".format(username, password)
			return HttpResponse("Invalid login details supplied.")
	else:
		return render(request, 'rango/login.html', {})
		
@login_required
def restricted(request):
    return render(request, 'rango/restricted.html',{})
	
@login_required
def user_logout(request):
	logout(request)
	return HttpResponseRedirect('/rango/')

def search(request):
    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            # Run our Bing function to get the results list!
            result_list = run_query(query)
            print result_list
    return render(request, 'rango/search.html', {'result_list': result_list})
	
def track_url(request):
    page_id = None
    url = '/rango/'
    if request.method == 'GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views = page.views + 1
                page.save()
                url = page.url
            except:
                pass

    return redirect(url)
	
@login_required
def like_category(request):

    cat_id = None
    print request
    if request.method == 'GET':
        cat_id = request.GET['category_id']

    likes = 0
    if cat_id:
        cat = Category.objects.get(id=int(cat_id))
        if cat:
            likes = cat.likes + 1
            cat.likes =  likes
            cat.save()

    return HttpResponse(likes)
	
def get_category_list(max_results=0, starts_with=''):
        cat_list = []
        if starts_with:
                cat_list = Category.objects.filter(name__istartswith=starts_with)

        if max_results > 0:
                if len(cat_list) > max_results:
                        cat_list = cat_list[:max_results]

        return cat_list
		
def suggest_category(request):

        cat_list = []
        starts_with = ''
        print starts_with
        if request.method == 'GET':
                starts_with = request.GET['suggestion']
                print starts_with
        cat_list = get_category_list(8, starts_with)
        print cat_list
        return render(request, 'rango/category_list.html', {'cat_list': cat_list })