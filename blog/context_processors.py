from django.db.models import Q

from .models import Message


def unread_conversations(request):

    if request.user.is_authenticated:

        unread = (
            Message.objects.filter(
                Q(conversation__buyer=request.user)
                | Q(conversation__seller=request.user),
                is_read=False,
            )
            .exclude(sender=request.user)
            .count()
        )

    else:
        unread = 0

    return {"unread_conversation_count": unread}
