from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.urls import reverse
from django.contrib.auth.forms import UserCreationForm
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from .models import Resource
from .forms import ResourceForm
import requests
from django.conf import settings



@login_required
def resource_detail(request, resource_id):
    resource_from_db = get_object_or_404(Resource, id=resource_id)
    return render(request, "resources/detail.html", {"resource": resource_from_db})


class RegisterView(View):
    def get(self, request):
        form = UserCreationForm()
        return render(request, "resources/register.html", {"form": form})

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("resource_list")
        return render(request, "resources/register.html", {"form": form})


class Home(LoginView):
    template_name = "resources/home.html"

    def get_success_url(self):
        return redirect("home")


class ResourceListView(LoginRequiredMixin, View):
    def get(self, request):
        query = request.GET.get("q")
        if request.GET.get("clear"):
            query = None
        if query:
            resources = Resource.objects.filter(
                user=request.user, name__icontains=query
            )
        else:
            resources = Resource.objects.filter(user=request.user)

        return render(
            request,
            "resources/resource_list.html",
            {"resources": resources, "query": query},
        )


class ResourceCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = ResourceForm()
        query = request.GET.get("query", "").strip()
        keyword = request.GET.get("keyword", "").strip()
        location = None
        resources = []
        error_message = None
        if query.isdigit():
            location = self.get_coordinates_from_zip(query)
            if not location:
                error_message = f"Could not retrieve location for ZIP code: {query}"
        if location:
            search_query = keyword if keyword else query
            resources = self.search_resources(search_query, location)
            if not resources:
                error_message = (
                    f"No resources found for '{search_query}' in this location."
                )
        return render(
            request,
            "resources/resource_form.html",
            {
                "form": form,
                "resources": resources,
                "query": query,
                "keyword": keyword,
                "location": location,
                "no_results": not resources,
                "error_message": error_message,
            },
        )

    def post(self, request):
        form = ResourceForm(request.POST)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.user = request.user
            resource.save()
            return redirect("resource_list")
        return render(
            request,
            "resources/resource_form.html",
            {
                "form": form,
                "error_message": "Please correct the errors below.",
            },
        )

    def get_coordinates_from_zip(self, zip_code):
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "key": settings.API_KEY,
            "address": zip_code,
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data["results"]:
                location = data["results"][0]["geometry"]["location"]
                return f"{location['lat']},{location['lng']}"
            else:
                return None
        except requests.exceptions.RequestException as e:
            return None

    def search_resources(self, query, location):
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        initial_radius = 5000 
        max_radius = 50000
        step_radius = 10000
        resources = []
        while initial_radius <= max_radius and not resources:
            params = {
                "key": settings.API_KEY,
                "location": location,
                "radius": initial_radius,
                "keyword": query,
                "type": "point_of_interest",
            }
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                if data.get("status") == "OK":
                    for place in data.get("results", []):
                        place_details = self.get_place_details(place.get("place_id"))
                        resources.append(
                            {
                                "name": place.get("name"),
                                "address": place.get("vicinity"),
                                "location": place.get("geometry", {}).get("location"),
                                "types": place.get("types"),
                                "phone_number": (
                                    place_details.get("formatted_phone_number")
                                    if place_details
                                    else None
                                ),
                            }
                        )
                elif data.get("status") == "ZERO_RESULTS":
                    initial_radius += step_radius
                else:
                    break
            except requests.exceptions.RequestException as e:
                break
        return resources

    def get_place_details(self, place_id):
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "key": settings.API_KEY,
            "place_id": place_id,
            "fields": "formatted_phone_number",
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "OK":
                return data.get("result", {})
            else:
                return None
        except requests.exceptions.RequestException as e:
            return None


class ResourceUpdateView(LoginRequiredMixin, View):
    def get(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        form = ResourceForm(instance=resource)
        return render(
            request,
            "resources/resource_form.html",
            {"form": form, "resource": resource},
        )

    def post(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        form = ResourceForm(request.POST, instance=resource)
        if form.is_valid():
            form.save()
            return redirect(reverse("resource-detail", args=[resource.id]))
        return render(
            request,
            "resources/resource_form.html",
            {"form": form, "resource": resource},
        )


class ResourceDeleteView(LoginRequiredMixin, View):
    def get(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        return render(
            request, "resources/resource_confirm_delete.html", {"object": resource}
        )

    def post(self, request, pk):
        resource = get_object_or_404(Resource, pk=pk)
        resource.delete()
        return redirect("resource_list")
