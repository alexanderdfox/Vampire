#!/bin/bash

# Target group and current user configuration
TARGET_GROUP="developers"
CURRENT_USER=$(whoami)
IDLE_THRESHOLD_MIN=30

echo "Initializing vampire monitor..."
echo "Current user ($CURRENT_USER) and group ($TARGET_GROUP) under surveillance."

# 1. Inspect the Current User
echo "--- Checking Current User: $CURRENT_USER ---"
current_user_sessions=$(who | grep "^$CURRENT_USER ")

if [ -n "$current_user_sessions" ]; then
    echo "Active session(s) found for $CURRENT_USER:"
    echo "$current_user_sessions"
    
    # Check processes owned by the current user
    # (Example drain: check top resource-consuming processes)
    echo "Top processes for $CURRENT_USER:"
    ps -u "$CURRENT_USER" -o pid,%cpu,%mem,comm --sort=-%cpu | head -n 4
else
    echo "No active sessions found for $CURRENT_USER."
fi

echo ""
echo "--- Checking Group: $TARGET_GROUP ---"

# 2. Inspect Group Users
GROUP_USERS=$(getent group "$TARGET_GROUP" | awk -F: '{print $4}')

for user in $(echo $GROUP_USERS | tr ',' ' '); do
    # Skip if the group member is already checked as the current user
    if [ "$user" == "$CURRENT_USER" ]; then
        continue
    }

    active_sessions=$(who | grep "^$user ")
    if [ -n "$active_sessions" ]; then
        echo "Found active group member: $user"
        idle_time=$(w -h | grep "^$user " | awk '{print $5}')
        echo "User $user idle status: $idle_time"
    fi
done
