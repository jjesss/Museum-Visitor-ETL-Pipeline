#!/bin/bash
# reset_db.sh - Clears visitor interaction data while preserving reference tables

set -e  # Exit on any error

# Load environment variables (DB credentials)
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env file not found"
    exit 1
fi
# Add a confirmation prompt
read -p "⚠️  This will DELETE all visitor interaction data. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo "Resetting visitor_interactions table..."

# Execute DELETE command
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d museum -c "DELETE FROM visitor_interactions;"

echo "✓ visitor_interactions table cleared"
echo "✓ button_type and exhibition tables preserved"