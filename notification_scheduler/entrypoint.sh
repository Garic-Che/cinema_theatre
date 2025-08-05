#!/bin/sh

exec uvicorn main:app --host $NOTIFICATION_SCHEDULER_HOST --port $NOTIFICATION_SCHEDULER_PORT --reload