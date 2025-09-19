from django.urls import path
from .views import HealthView, PredictView, ModelInfoView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health"),
    path("model-info/", ModelInfoView.as_view(), name="model_info"),  # جديد
    path("predict/", PredictView.as_view(), name="predict"),
]
