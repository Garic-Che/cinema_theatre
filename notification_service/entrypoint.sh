#!/bin/sh

uvicorn main:app --host $NOTIFICATION_SERVICE_HOST --port $NOTIFICATION_SERVICE_PORT --reload

exec "$@"