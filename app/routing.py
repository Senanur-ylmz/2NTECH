from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from app.consumers import ChatConsumer
application = ProtocolTypeRouter({
    'websocket': URLRouter([
        path('ws/app/', ChatConsumer.as_asgi()),
    ])
})