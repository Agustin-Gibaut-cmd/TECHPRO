from django.urls import path

from .views import RepairListCreateView, RepairUpdateView

urlpatterns = [
    path("", RepairListCreateView.as_view(), name="repair-list-create"),
    path("<int:pk>/", RepairUpdateView.as_view(), name="repair-update"),
]
