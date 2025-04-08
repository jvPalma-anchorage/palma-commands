#!/bin/bash
# Configuration based on the FEED variable
FEED="serie1"

declare -A FILE_MAP=(
  ["serie1"]="serie1.json"
  ["serie2"]="serie2.json"
)
declare -A QUERY_MAP=(
  ["serie1"]="?q=s%C3%A9rie:1"
  ["serie2"]="?q=s%C3%A9rie:2"
)
declare -A TITLE_MAP=(
  ["serie1"]="DRE Série 1"
  ["serie2"]="DRE Série 2"
)

FILE="${FILE_MAP[$FEED]}"
Q="${QUERY_MAP[$FEED]}"
TITLE="${TITLE_MAP[$FEED]}"

RSS_URL="https://dre.tretas.org/dre/rss/${Q}"

# Array of user agents
userAgents=(
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/58.0.3029.110 Safari/537.36"
  "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Safari/605.1.15"
  "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Firefox/64.0 Safari/537.36"
)

tries=0
success=false

# Create a temporary file for the RSS XML
temp_xml=$(mktemp)

while [ "$success" = false ]; do
  ((tries++))
  # Pick a random user agent
  random_index=$(( RANDOM % ${#userAgents[@]} ))
  userAgent="${userAgents[$random_index]}"

  # Fetch the RSS feed with a 10-second timeout using curl
  curl --max-time 10 -s -H "User-Agent: $userAgent" "$RSS_URL" -o "$temp_xml"

  if [ $? -ne 0 ] || [ ! -s "$temp_xml" ]; then
    echo "Error fetching RSS feed. Number of tries: $tries"
    continue
  fi

  # # Validate the XML using xmlstarlet
  # xmlstarlet val -w "$temp_xml" >/dev/null 2>&1
  # if [ $? -ne 0 ]; then
  #   echo "Error: downloaded RSS feed is not valid XML. Number of tries: $tries"
  #   continue
  # fi

  success=true
done

# Print the <channel> element for debugging
echo "Channel element:"
xmlstarlet sel -t -c "/rss/channel" "$temp_xml"

# Extract the channel description
chan_description=$(xmlstarlet sel -t -v "/rss/channel/description" "$temp_xml")

# Build the JSON array for items.
# For each <item> the fields: guid, title, description, dc:creator and pubDate are extracted.
# The pubDate is processed to add 11 days; if date conversion fails, the original string is used.
items_json=$(xmlstarlet sel -N dc="http://purl.org/dc/elements/1.1/" \
  -t -m "/rss/channel/item" \
  -v "concat(guid, '|||', title, '|||', description, '|||', dc:creator, '|||', pubDate)" -n "$temp_xml" | \
  while IFS='|||'
  read -r guid title desc creator pubDate; do
    new_pubDate=$(date -d "$pubDate + 11 days" +"%Y-%m-%dT%H-%M-%S.000" 2>/dev/null || echo "$pubDate")
    jq -n --arg id "$guid" --arg title "$title" --arg description "$desc" --arg creator "$creator" --arg pubDate "$new_pubDate" \
      '{id: $id, title: $title, description: $description, creator: $creator, pubDate: $pubDate}'
  done)

# Combine all items into a JSON array
items_array=$(echo "$items_json" | paste -sd, -)

# Assemble the final JSON object with the title, channel description, and items array
final_json=$(jq -n --arg title "$TITLE" --arg description "$chan_description" --argjson items "[$items_array]" \
  '{title: $title, description: $description, items: $items}')

# Save the final JSON to the output file
echo "$final_json" > "$FILE"
echo "RSS feed parsed and saved to $FILE"

# Clean up the temporary XML file
rm "$temp_xml"
