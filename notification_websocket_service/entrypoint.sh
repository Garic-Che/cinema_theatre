#!/bin/sh

exec uvicorn main:app --host $WEBSOCKET_HOST --port $WEBSOCKET_PORT --reload