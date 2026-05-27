# Project Context: AI-Powered Restaurant Recommendation System

## Overview

Build an **AI-powered restaurant recommendation service** inspired by **Zomato**. The system suggests restaurants from a real-world dataset by combining **structured filtering** with a **Large Language Model (LLM)** to produce personalized, human-like recommendations.

## Objective

Design and implement an application that:

1. Accepts **user preferences** (location, budget, cuisine, ratings, and more)
2. Uses a **real-world restaurant dataset**
3. Leverages an **LLM** for personalized, natural-language recommendations
4. **Displays** clear, useful results to the user

## Data Source

| Item | Detail |
|------|--------|
| **Dataset** | Zomato restaurant data on Hugging Face |
| **URL** | https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation |
| **Relevant fields** | Restaurant name, location, cuisine, cost, rating, and related attributes |

### Data Ingestion Responsibilities

- Load and preprocess the dataset from Hugging Face
- Extract fields needed for filtering and display (name, location, cuisine, cost, rating, etc.)

## User Input

Collect preferences including:

| Preference | Examples / Notes |
|------------|------------------|
| **Location** | Delhi, Bangalore |
| **Budget** | low, medium, high |
| **Cuisine** | Italian, Chinese |
| **Minimum rating** | Numeric threshold |
| **Additional** | family-friendly, quick service, etc. |

## System Architecture & Workflow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  Data Ingestion │ ──► │   User Input     │ ──► │ Integration Layer   │
│  (Hugging Face) │     │  (preferences)   │     │ filter + LLM prompt │
└─────────────────┘     └──────────────────┘     └──────────┬──────────┘
                                                            │
                                                            ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│ Output Display  │ ◄── │ Recommendation   │ ◄── │       LLM         │
│  (top picks)    │     │     Engine       │     │ rank + explain      │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
```

### 1. Data Ingestion

- Load and preprocess the Zomato dataset from Hugging Face
- Extract structured fields for downstream filtering and UI

### 2. User Input

- Capture location, budget, cuisine, minimum rating, and optional free-form preferences

### 3. Integration Layer

- **Filter** restaurant records to match user input
- **Prepare** structured candidate results for the LLM
- **Design a prompt** so the LLM can reason over and rank options

### 4. Recommendation Engine (LLM)

The LLM should:

- **Rank** restaurants against user preferences
- **Explain** why each recommendation fits
- **Optionally** summarize the overall set of choices

### 5. Output Display

Present **top recommendations** in a user-friendly format. Each result should include:

| Field | Description |
|-------|-------------|
| Restaurant name | From dataset |
| Cuisine | From dataset |
| Rating | From dataset |
| Estimated cost | From dataset |
| AI-generated explanation | From LLM (why it matches preferences) |

## Technical Considerations (Implied)

- **Structured pipeline first**: filter dataset by hard constraints (location, budget band, cuisine, min rating) before LLM calls to limit tokens and improve relevance
- **Prompt design**: pass filtered candidates as structured context; instruct ranking, justification, and optional summary
- **LLM integration**: choose provider/API, handle errors, and bound response format for reliable UI parsing if needed
- **UX**: clear input form and readable recommendation cards or list with explanations

## Success Criteria

- End-to-end flow: preferences in → filtered data → LLM reasoning → displayed top picks with explanations
- Recommendations feel **personalized** and **explainable**, not only rule-based filtering
- Output is **actionable** for a user choosing where to eat (name, cuisine, rating, cost, and why it fits)

## Reference

- Full problem statement: [`docs/problemStatement.txt`](./problemStatement.txt)
