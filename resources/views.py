from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from .models import Resource
from .forms import ResourceForm


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
    template_name = "registration/login.html"

    def get_success_url(self):
        return redirect("resource_list")


class ResourceListView(LoginRequiredMixin, View):
    def get(self, request):
        resources = Resource.objects.filter(user=request.user)
        return render(request, "resources/resource_list.html", {"resources": resources})


class ResourceCreateView(LoginRequiredMixin, View):
    def get(self, request):
        form = ResourceForm()
        return render(request, "resources/resource_form.html", {"form": form})

    def post(self, request):
        form = ResourceForm(request.POST)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.user = request.user
            resource.save()
            return redirect("resource_list")
        return render(request, "resources/resource_form.html", {"form": form})


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
            return redirect("resource_list")
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
