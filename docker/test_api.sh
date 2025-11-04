#!/bin/bash
TOKEN=$(cat /tmp/token.txt)
curl -s -X POST http://localhost:9000/developer/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task":"Write a simple Python function to add two numbers","project_id":"test-project-001","workflow_id":"cost-tracking-test"}' \
  | jq .
