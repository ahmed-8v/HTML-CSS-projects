from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from django.forms import modelformset_factory
from .models import Ad, Category, AdImage, Contact
from .forms import CustomUserCreationForm, AdForm, AdImageForm, ContactForm, SearchForm


def home(request):
    """Homepage view with search functionality"""
    ads = Ad.objects.filter(is_active=True).select_related('category', 'seller').prefetch_related('images')
    categories = Category.objects.all()
    form = SearchForm(request.GET)
    
    # Apply search filters
    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        
        if query:
            ads = ads.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query)
            )
        
        if category:
            ads = ads.filter(category=category)
        
        if min_price:
            ads = ads.filter(price__gte=min_price)
        
        if max_price:
            ads = ads.filter(price__lte=max_price)
    
    # Pagination
    paginator = Paginator(ads, 12)  # Show 12 ads per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'form': form,
        'total_ads': ads.count(),
    }
    
    return render(request, 'ads/home.html', context)


def register_view(request):
    """User registration view"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            login(request, user)  # Auto-login after registration
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def ad_detail(request, pk):
    """Ad detail view with contact form"""
    ad = get_object_or_404(Ad, pk=pk, is_active=True)
    images = ad.images.all()
    
    # Handle contact form submission
    if request.method == 'POST':
        contact_form = ContactForm(request.POST)
        if contact_form.is_valid():
            contact = contact_form.save(commit=False)
            contact.ad = ad
            contact.save()
            
            # Send email to seller (optional - configure email settings)
            try:
                send_mail(
                    subject=f'Interest in your ad: {ad.title}',
                    message=f"""
                    Someone is interested in your ad "{ad.title}".
                    
                    From: {contact.sender_name} ({contact.sender_email})
                    Message: {contact.message}
                    
                    Ad Link: {request.build_absolute_uri(ad.get_absolute_url() if hasattr(ad, 'get_absolute_url') else f'/ad/{ad.pk}/')}
                    """,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[ad.seller.email],
                    fail_silently=True,
                )
            except Exception as e:
                pass  # Email sending failed, but continue
            
            messages.success(request, 'Your message has been sent to the seller!')
            return redirect('ad_detail', pk=ad.pk)
    else:
        contact_form = ContactForm()
    
    context = {
        'ad': ad,
        'images': images,
        'contact_form': contact_form,
    }
    
    return render(request, 'ads/ad_detail.html', context)


@login_required
def create_ad(request):
    """Create new ad view"""
    ImageFormSet = modelformset_factory(AdImage, form=AdImageForm, extra=5, max_num=5)
    
    if request.method == 'POST':
        ad_form = AdForm(request.POST)
        image_formset = ImageFormSet(request.POST, request.FILES, queryset=AdImage.objects.none())
        
        if ad_form.is_valid() and image_formset.is_valid():
            ad = ad_form.save(commit=False)
            ad.seller = request.user
            ad.save()
            
            # Save images
            for form in image_formset:
                if form.cleaned_data.get('image'):
                    image = form.save(commit=False)
                    image.ad = ad
                    image.save()
            
            messages.success(request, 'Your ad has been created successfully!')
            return redirect('ad_detail', pk=ad.pk)
    else:
        ad_form = AdForm()
        image_formset = ImageFormSet(queryset=AdImage.objects.none())
    
    context = {
        'ad_form': ad_form,
        'image_formset': image_formset,
    }
    
    return render(request, 'ads/create_ad.html', context)


@login_required
def edit_ad(request, pk):
    """Edit ad view"""
    ad = get_object_or_404(Ad, pk=pk, seller=request.user)
    ImageFormSet = modelformset_factory(AdImage, form=AdImageForm, extra=1, max_num=5, can_delete=True)
    
    if request.method == 'POST':
        ad_form = AdForm(request.POST, instance=ad)
        image_formset = ImageFormSet(request.POST, request.FILES, queryset=ad.images.all())
        
        if ad_form.is_valid() and image_formset.is_valid():
            ad_form.save()
            
            # Save images
            for form in image_formset:
                if form.cleaned_data.get('DELETE'):
                    if form.instance.pk:
                        form.instance.delete()
                elif form.cleaned_data.get('image'):
                    image = form.save(commit=False)
                    image.ad = ad
                    image.save()
            
            messages.success(request, 'Your ad has been updated successfully!')
            return redirect('ad_detail', pk=ad.pk)
    else:
        ad_form = AdForm(instance=ad)
        image_formset = ImageFormSet(queryset=ad.images.all())
    
    context = {
        'ad_form': ad_form,
        'image_formset': image_formset,
        'ad': ad,
    }
    
    return render(request, 'ads/edit_ad.html', context)


@login_required
def delete_ad(request, pk):
    """Delete ad view"""
    ad = get_object_or_404(Ad, pk=pk, seller=request.user)
    
    if request.method == 'POST':
        ad.delete()
        messages.success(request, 'Your ad has been deleted successfully!')
        return redirect('my_ads')
    
    return render(request, 'ads/delete_ad.html', {'ad': ad})


@login_required
def my_ads(request):
    """View user's own ads"""
    ads = Ad.objects.filter(seller=request.user).prefetch_related('images')
    
    # Pagination
    paginator = Paginator(ads, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'ads/my_ads.html', context)


def category_view(request, category_id):
    """View ads by category"""
    category = get_object_or_404(Category, pk=category_id)
    ads = Ad.objects.filter(category=category, is_active=True).select_related('seller').prefetch_related('images')
    
    # Pagination
    paginator = Paginator(ads, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    
    return render(request, 'ads/category.html', context)