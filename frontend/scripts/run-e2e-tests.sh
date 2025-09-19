#!/bin/bash

# E2E Test Runner Script for Mail Score Backend Dashboard
# Usage: ./scripts/run-e2e-tests.sh [test-type] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
BROWSER="chromium"
HEADED=false
DEBUG=false
UI_MODE=false

# Help function
show_help() {
    echo "E2E Test Runner for Mail Score Dashboard"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -t, --test TYPE     Test type: all, sql, dashboard, responsive (default: all)"
    echo "  -b, --browser NAME  Browser: chromium, firefox, webkit, mobile (default: chromium)"
    echo "  -h, --headed        Run in headed mode (show browser)"
    echo "  -d, --debug         Run in debug mode"
    echo "  -u, --ui            Run in UI mode"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Run all tests"
    echo "  $0 -t sql -h                # Run SQL tests in headed mode"
    echo "  $0 -t responsive -b firefox  # Run responsive tests in Firefox"
    echo "  $0 -d                        # Run all tests in debug mode"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--test)
            TEST_TYPE="$2"
            shift 2
            ;;
        -b|--browser)
            BROWSER="$2"
            shift 2
            ;;
        -h|--headed)
            HEADED=true
            shift
            ;;
        -d|--debug)
            DEBUG=true
            shift
            ;;
        -u|--ui)
            UI_MODE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Function to check if development server is running
check_dev_server() {
    echo -e "${BLUE}Checking if development server is running...${NC}"

    if curl -s http://localhost:3000 > /dev/null; then
        echo -e "${GREEN}✓ Development server is running${NC}"
        return 0
    else
        echo -e "${RED}✗ Development server is not running${NC}"
        echo -e "${YELLOW}Please start the development server with: npm run dev${NC}"
        return 1
    fi
}

# Function to install Playwright browsers if needed
install_browsers() {
    echo -e "${BLUE}Checking Playwright browser installation...${NC}"

    if ! npx playwright install --dry-run > /dev/null 2>&1; then
        echo -e "${YELLOW}Installing Playwright browsers...${NC}"
        npx playwright install
        echo -e "${GREEN}✓ Playwright browsers installed${NC}"
    else
        echo -e "${GREEN}✓ Playwright browsers are already installed${NC}"
    fi
}

# Function to build test command
build_command() {
    local cmd="npx playwright test"

    # Add test file pattern
    case $TEST_TYPE in
        sql)
            cmd="$cmd sql-execution"
            ;;
        dashboard)
            cmd="$cmd dashboard"
            ;;
        responsive)
            cmd="$cmd responsive"
            ;;
        all)
            # Run all tests
            ;;
        *)
            echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
            echo "Valid types: all, sql, dashboard, responsive"
            exit 1
            ;;
    esac

    # Add browser selection
    if [[ $BROWSER != "chromium" ]]; then
        case $BROWSER in
            firefox)
                cmd="$cmd --project=firefox"
                ;;
            webkit)
                cmd="$cmd --project=webkit"
                ;;
            mobile)
                cmd="$cmd --project='Mobile Chrome'"
                ;;
            *)
                echo -e "${RED}Unknown browser: $BROWSER${NC}"
                echo "Valid browsers: chromium, firefox, webkit, mobile"
                exit 1
                ;;
        esac
    fi

    # Add mode flags
    if [[ $DEBUG == true ]]; then
        cmd="$cmd --debug"
    elif [[ $UI_MODE == true ]]; then
        cmd="$cmd --ui"
    elif [[ $HEADED == true ]]; then
        cmd="$cmd --headed"
    fi

    echo "$cmd"
}

# Main execution
main() {
    echo -e "${BLUE}🧪 Mail Score Dashboard E2E Tests${NC}"
    echo -e "${BLUE}====================================${NC}"

    # Pre-flight checks
    if ! check_dev_server; then
        exit 1
    fi

    install_browsers

    # Build and execute command
    local test_cmd=$(build_command)

    echo -e "${BLUE}Running tests with configuration:${NC}"
    echo -e "  Test Type: ${YELLOW}$TEST_TYPE${NC}"
    echo -e "  Browser: ${YELLOW}$BROWSER${NC}"
    echo -e "  Mode: ${YELLOW}$(if [[ $DEBUG == true ]]; then echo "debug"; elif [[ $UI_MODE == true ]]; then echo "ui"; elif [[ $HEADED == true ]]; then echo "headed"; else echo "headless"; fi)${NC}"
    echo ""

    echo -e "${BLUE}Executing: ${YELLOW}$test_cmd${NC}"
    echo ""

    # Run the tests
    if eval "$test_cmd"; then
        echo ""
        echo -e "${GREEN}✅ Tests completed successfully!${NC}"

        # Show report if not in debug/ui mode
        if [[ $DEBUG != true && $UI_MODE != true ]]; then
            echo -e "${BLUE}Opening test report...${NC}"
            npx playwright show-report
        fi
    else
        echo ""
        echo -e "${RED}❌ Tests failed!${NC}"
        echo -e "${YELLOW}Check the output above for details${NC}"
        echo -e "${YELLOW}You can also run: npm run test:e2e:report${NC}"
        exit 1
    fi
}

# Run if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi