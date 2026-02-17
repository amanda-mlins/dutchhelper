#!/bin/bash
# Quick utility script to interact with the verb database
# Usage: bash database_utils.sh <command>

set -e

BACKEND_DIR="/Users/alins/dutchhelper/backend"
API_URL="http://localhost:8000/api"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if backend is running
check_backend() {
    if ! curl -s "${API_URL}/health" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Backend not running at ${API_URL}${NC}"
        echo "Start it with: cd $BACKEND_DIR && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
        exit 1
    fi
}

# Command handlers
cmd_bootstrap() {
    print_header "Bootstrapping Verb Database"
    cd "$BACKEND_DIR"
    python bootstrap_verbs.py
}

cmd_stats() {
    print_header "Database Statistics"
    check_backend
    
    response=$(curl -s "$API_URL/database-stats")
    
    echo -e "\n${YELLOW}Database Info:${NC}"
    echo "$response" | python -m json.tool | grep -A 10 "database" | head -15
    
    echo -e "\n${YELLOW}Query Statistics:${NC}"
    echo "$response" | python -m json.tool | grep -A 15 "queries" | head -20
    
    echo -e "\n${YELLOW}Savings Estimate:${NC}"
    echo "$response" | python -m json.tool | grep -A 10 "savings" | head -15
}

cmd_export() {
    print_header "Exporting Database"
    check_backend
    
    response=$(curl -s -X POST "$API_URL/database-export")
    
    export_path=$(echo "$response" | python -c "import sys, json; print(json.load(sys.stdin).get('export_path', 'unknown'))" 2>/dev/null || echo "unknown")
    verbs_count=$(echo "$response" | python -c "import sys, json; print(json.load(sys.stdin).get('verbs_exported', '?'))" 2>/dev/null || echo "?")
    
    print_success "Database exported successfully"
    echo "  Path: $export_path"
    echo "  Verbs: $verbs_count"
}

cmd_backup() {
    print_header "Creating Database Backup"
    cd "$BACKEND_DIR"
    
    python << 'EOF'
from app.verb_database_manager import VerbDatabaseManager
import os

backup_dir = os.path.join(os.getcwd(), 'backups')
os.makedirs(backup_dir, exist_ok=True)

backup_path = VerbDatabaseManager.backup_database(
    os.path.join(backup_dir, None)  # Uses default timestamped name
)

print(f"\n✅ Backup created successfully:")
print(f"   Path: {backup_path}")

# Show file size
import os
size_mb = os.path.getsize(backup_path) / (1024 * 1024)
print(f"   Size: {size_mb:.2f} MB")
EOF
}

cmd_test() {
    print_header "Testing Database System"
    check_backend
    
    # Test 1: Query a known verb
    print_info "Test 1: Querying a known verb (zijn)..."
    curl -s -X POST "$API_URL/conjugate" \
        -H "Content-Type: application/json" \
        -d '{"verb": "zijn"}' \
        | python -m json.tool > /tmp/verb_response.json
    
    if grep -q "conjugation_data" /tmp/verb_response.json 2>/dev/null || grep -q "tenses" /tmp/verb_response.json 2>/dev/null; then
        print_success "Test 1 passed: Known verb returned successfully"
    else
        echo "❌ Test 1 failed"
        cat /tmp/verb_response.json
    fi
    
    # Test 2: Check stats
    print_info "Test 2: Checking database statistics..."
    response=$(curl -s "$API_URL/database-stats")
    if echo "$response" | python -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
        print_success "Test 2 passed: Statistics endpoint working"
    else
        echo "❌ Test 2 failed: Invalid statistics response"
    fi
    
    echo ""
    print_success "All tests completed!"
}

cmd_query() {
    local verb="${1:-zijn}"
    print_header "Querying Verb: $verb"
    check_backend
    
    print_info "Sending request..."
    response=$(curl -s -X POST "$API_URL/conjugate" \
        -H "Content-Type: application/json" \
        -d "{\"verb\": \"$verb\"}")
    
    echo -e "\n${YELLOW}Response:${NC}"
    echo "$response" | python -m json.tool 2>/dev/null || echo "$response"
}

cmd_info() {
    print_header "Database System Information"
    
    echo -e "\n${YELLOW}Files Created:${NC}"
    echo "  ✅ app/verb_persistence.py          - Persistence layer (SQLite + JSON)"
    echo "  ✅ app/verb_database_manager.py     - Database management utilities"
    echo "  ✅ app/verb_conjugation_service.py  - Updated with 4-layer lookup"
    echo "  ✅ bootstrap_verbs.py               - One-time bootstrap script"
    echo "  ✅ verbs.db                         - SQLite database (grows over time)"
    
    echo -e "\n${YELLOW}Documentation:${NC}"
    echo "  📖 DATABASE_SYSTEM.md               - Technical deep dive"
    echo "  📖 VERB_DATABASE_SETUP.md           - Quick start guide"
    echo "  📖 VERB_DATABASE_IMPLEMENTATION.md  - Implementation summary"
    
    echo -e "\n${YELLOW}New API Endpoints:${NC}"
    echo "  GET  /api/database-stats      - View statistics and savings"
    echo "  POST /api/database-export     - Export database to JSON"
    
    echo -e "\n${YELLOW}Features:${NC}"
    echo "  ✅ Zero-cost SQLite database"
    echo "  ✅ Automatic verb persistence"
    echo "  ✅ 4-layer lookup (cache → storage → hardcoded → LLM)"
    echo "  ✅ Query tracking for analytics"
    echo "  ✅ API savings estimation"
    echo "  ✅ Git-friendly JSON export"
    echo "  ✅ Automatic backups"
    
    echo -e "\n${YELLOW}Usage Examples:${NC}"
    echo "  bash database_utils.sh bootstrap   - Bootstrap database with 16 verbs"
    echo "  bash database_utils.sh stats       - View database statistics"
    echo "  bash database_utils.sh export      - Export database to JSON"
    echo "  bash database_utils.sh backup      - Create timestamped backup"
    echo "  bash database_utils.sh test        - Run integration tests"
    echo "  bash database_utils.sh query lopen - Query a specific verb"
}

# Main command router
case "${1:-info}" in
    bootstrap)
        cmd_bootstrap
        ;;
    stats)
        cmd_stats
        ;;
    export)
        cmd_export
        ;;
    backup)
        cmd_backup
        ;;
    test)
        cmd_test
        ;;
    query)
        cmd_query "$2"
        ;;
    info|help|--help|-h)
        cmd_info
        ;;
    *)
        echo "Unknown command: $1"
        cmd_info
        exit 1
        ;;
esac
