from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .serializers import SubmissionCreateSerializer
from .throttles import SubmissionIPThrottle, SubmissionWidgetThrottle
from .enrichment import enrich_ip
from .side_effects import send_confirmation
from .models import Submission


def get_client_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


class SubmissionCreateView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [SubmissionIPThrottle, SubmissionWidgetThrottle]

    def post(self, request):
        serializer = SubmissionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        widget = serializer.widget
        validated = serializer.validated_data

        if validated.get('hp_field'):
            # Honeypot tripped — fake a normal success, don't tell the bot why it "failed"
            return Response({'id': None, 'status': 'received'}, status=status.HTTP_201_CREATED)

        ip = get_client_ip(request)
        geo = enrich_ip(ip)

        submission = Submission.objects.create(
            tenant=widget.tenant,
            widget=widget,
            data=validated['data'],
            ip_address=ip,
            country=geo['country'],
            city=geo['city'],
            geo_provider_used=geo['provider'],
        )

        try:
            submission.side_effect_sent = send_confirmation(submission)
        except Exception:
            submission.side_effect_sent = False
            submission.save(update_fields=['side_effect_sent'])

        return Response({'id': str(submission.id), 'status': 'received'}, status=status.HTTP_201_CREATED)
            