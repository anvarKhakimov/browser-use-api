#!/bin/bash

# Simple Browser-Use CLI wrapper
# A lightweight bash alternative to the Python CLI

# Configuration
API_URL="${BRO_API_URL:-http://localhost:8765/api/v1/search}"
MAX_STEPS="${BRO_MAX_STEPS:-10}"
TIMEOUT="${BRO_TIMEOUT:-120}"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m' # No Color

# Help function
show_help() {
    echo -e "${BOLD}${BLUE}Browser-Use CLI Tool${NC}"
    echo -e "${DIM}Simple bash wrapper for Browser-Use API${NC}"
    echo
    echo -e "${BOLD}Usage:${NC}"
    echo "  bro <task>              Execute a browser task"
    echo "  bro --help              Show this help message"
    echo
    echo -e "${BOLD}Examples:${NC}"
    echo "  bro find top news on BBC"
    echo "  bro go to example.com"
    echo "  bro search for latest AI news"
    echo
    echo -e "${BOLD}Configuration:${NC}"
    echo "  API URL: $API_URL"
    echo "  Max Steps: $MAX_STEPS"
    echo "  Timeout: ${TIMEOUT}s"
    echo
    echo -e "${DIM}Set environment variables to override:${NC}"
    echo -e "${DIM}  export BRO_API_URL=http://localhost:8765/api/v1/search${NC}"
    echo -e "${DIM}  export BRO_MAX_STEPS=10${NC}"
    echo -e "${DIM}  export BRO_TIMEOUT=120${NC}"
}

# Check for help flag
if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

# Join all arguments as task
TASK="$*"

# Display task
echo
echo -e "${BOLD}${BLUE}Task:${NC} $TASK"
echo -e "${DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}⏳ Processing...${NC}"
echo

# Prepare JSON payload
JSON_PAYLOAD=$(cat <<EOF
{
    "task": "$TASK",
    "max_steps": $MAX_STEPS,
    "timeout": $TIMEOUT
}
EOF
)

# Send request and capture response
RESPONSE=$(curl -s -X POST "$API_URL" \
    -H "Content-Type: application/json" \
    -d "$JSON_PAYLOAD" 2>/dev/null)

# Check if curl failed
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Error${NC}"
    echo -e "${DIM}Failed to connect to Browser-Use API at $API_URL${NC}"
    echo -e "${DIM}Is the service running?${NC}"
    exit 1
fi

# Check if response is empty
if [ -z "$RESPONSE" ]; then
    echo -e "${RED}✗ Error${NC}"
    echo -e "${DIM}Empty response from API${NC}"
    exit 1
fi

# Parse response using Python (most systems have Python)
parse_response() {
    python3 -c "
import sys, json
try:
    data = json.loads(sys.stdin.read())
    status = data.get('status', 'unknown')

    if status == 'success':
        print('SUCCESS')
        print(data.get('result', 'No result'))
        print('STEPS:', data.get('steps_taken', 0))
        print('TIME:', data.get('execution_time', 0))
        urls = data.get('urls_visited', [])
        if urls:
            print('URLS:', '|'.join(urls))
    elif status == 'timeout':
        print('TIMEOUT')
        print(data.get('error_message', 'Task exceeded timeout'))
    elif status == 'failed':
        print('FAILED')
        print(data.get('error_message', 'Task failed'))
    else:
        print('ERROR')
        print(data.get('error_message', 'Unknown error'))
except Exception as e:
    print('ERROR')
    print(f'Failed to parse response: {e}')
" 2>/dev/null
}

# Parse and display the response
PARSED=$(echo "$RESPONSE" | parse_response)

if [ $? -ne 0 ] || [ -z "$PARSED" ]; then
    echo -e "${RED}✗ Error${NC}"
    echo -e "${DIM}Failed to parse API response${NC}"
    echo -e "${DIM}Raw response: $RESPONSE${NC}"
    exit 1
fi

# Process parsed response
STATUS=$(echo "$PARSED" | head -n1)
CONTENT=$(echo "$PARSED" | tail -n+2)

case "$STATUS" in
    "SUCCESS")
        echo -e "${GREEN}✓ Task completed successfully!${NC}"
        echo

        # Extract result
        RESULT=$(echo "$CONTENT" | grep -v "^STEPS:" | grep -v "^TIME:" | grep -v "^URLS:" | head -n-3)
        if [ -n "$RESULT" ]; then
            echo -e "${BOLD}Result:${NC}"
            echo -e "$RESULT"
            echo
        fi

        # Extract metadata
        STEPS=$(echo "$CONTENT" | grep "^STEPS:" | cut -d' ' -f2)
        TIME=$(echo "$CONTENT" | grep "^TIME:" | cut -d' ' -f2)
        URLS=$(echo "$CONTENT" | grep "^URLS:" | cut -d' ' -f2-)

        echo -e "${DIM}• Steps: $STEPS | Time: ${TIME}s${NC}"

        # Display URLs if present
        if [ -n "$URLS" ] && [ "$URLS" != "URLS:" ]; then
            echo
            echo -e "${BOLD}URLs visited:${NC}"
            IFS='|' read -ra URL_ARRAY <<< "$URLS"
            for url in "${URL_ARRAY[@]}"; do
                echo "  $url"
            done
        fi
        ;;

    "TIMEOUT")
        echo -e "${YELLOW}⏱ Task timed out${NC}"
        ERROR_MSG=$(echo "$CONTENT" | head -n1)
        echo -e "${DIM}$ERROR_MSG${NC}"
        exit 1
        ;;

    "FAILED")
        echo -e "${RED}✗ Task failed${NC}"
        ERROR_MSG=$(echo "$CONTENT" | head -n1)
        echo -e "${DIM}$ERROR_MSG${NC}"
        exit 1
        ;;

    *)
        echo -e "${RED}✗ Error${NC}"
        ERROR_MSG=$(echo "$CONTENT" | head -n1)
        echo -e "${DIM}$ERROR_MSG${NC}"
        exit 1
        ;;
esac

echo