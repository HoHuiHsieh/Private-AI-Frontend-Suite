#!/bin/bash
# filepath: /workspace/start.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if an argument is provided
if [ $# -eq 0 ]; then
    echo -e "${RED}Error: No argument provided${NC}"
    echo ""
    echo -e "${BLUE}Usage: $0 [dev|prod|down]${NC}"
    echo ""
    echo "Commands:"
    echo "  dev         - Start all services in development mode"
    echo "  prod        - Start all services in production mode"
    echo "  down        - Stop all services"
    echo ""
    exit 1
fi

# Start the container based on the argument
case "$1" in
  dev)
    echo -e "${GREEN}Starting all services in development mode...${NC}"
    echo ""
    
    # Load environment variables from .env.dev
    if [ -f .env.dev ]; then
      set -a
      source .env.dev
      set +a
      echo -e "${GREEN}✓ Loaded environment variables from .env.dev${NC}"
    else
      echo -e "${RED}Error: .env.dev file not found${NC}"
      exit 1
    fi

    # Start services with the dev profile
    docker compose --profile dev up -d --build
    echo ""
    echo -e "${GREEN}✓ Development services started successfully!${NC}"
    echo ""
    ;;

  prod)
    echo -e "${GREEN}Starting all services in production mode...${NC}"
    echo ""
    
    # Load environment variables from .env.prod
    if [ -f .env.prod ]; then
      set -a
      source .env.prod
      set +a
      echo -e "${GREEN}✓ Loaded environment variables from .env.prod${NC}"
    else
      echo -e "${RED}Error: .env.prod file not found${NC}"
      exit 1
    fi
    
    # Start services with the prod profile
    docker compose --profile prod up -d --build
    echo ""
    echo -e "${GREEN}✓ Production services started successfully!${NC}"
    echo ""
    ;;

  down)
    echo -e "${GREEN}Stopping all services...${NC}"
    echo ""
    
    # Stop all services
    docker compose --profile dev --profile prod down
    echo ""
    echo -e "${GREEN}✓ Services stopped successfully!${NC}"
    echo ""
    ;;

  *)
    echo -e "${RED}Error: Invalid argument '$1'${NC}"
    echo ""
    echo -e "${BLUE}Usage: $0 [dev|prod|down]${NC}"
    echo ""
    echo "Commands:"
    echo "  dev         - Start all services in development mode"
    echo "  prod        - Start all services in production mode"
    echo "  down        - Stop all services"
    echo ""
    exit 1
    ;;
esac
