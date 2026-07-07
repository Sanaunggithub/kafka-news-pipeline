#!/usr/bin/env bash
set -euo pipefail

BASE_URL="http://localhost:8000/news"

echo "Sending tech article..."
curl -sS -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{"id":"tech-001","title":"Tech firms expand AI chip production","content":"Major technology companies are investing heavily in new AI chip manufacturing facilities to meet rising demand for advanced computing infrastructure.","source":"Reuters","timestamp":"2026-07-07T10:00:00Z"}'
echo
sleep 1

echo "Sending business article..."
curl -sS -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{"id":"business-001","title":"Global markets rebound on strong corporate earnings","content":"Businesses reported stronger-than-expected quarterly earnings, lifting investor confidence and pushing major indices higher across global markets.","source":"Bloomberg","timestamp":"2026-07-07T10:00:30Z"}'
echo
sleep 1

echo "Sending health article..."
curl -sS -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{"id":"health-001","title":"New public health initiative targets respiratory diseases","content":"Health officials announced a new initiative focused on reducing respiratory infections through vaccination campaigns and public education programs.","source":"BBC","timestamp":"2026-07-07T10:01:00Z"}'
echo
sleep 1

echo "Sending politics article..."
curl -sS -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{"id":"politics-001","title":"Lawmakers debate new digital privacy legislation","content":"Government lawmakers are preparing to debate proposed digital privacy regulations aimed at strengthening data protections for citizens and businesses.","source":"CNN","timestamp":"2026-07-07T10:01:30Z"}'
echo
sleep 1

echo "Sending AI article..."
curl -sS -X POST "$BASE_URL" \
  -H "Content-Type: application/json" \
  -d '{"id":"ai-001","title":"Startups launch new tools for enterprise AI automation","content":"Artificial intelligence startups unveiled several new enterprise tools designed to help companies automate workflows and improve decision-making processes.","source":"TechCrunch","timestamp":"2026-07-07T10:02:00Z"}'
echo

echo "All articles sent!"