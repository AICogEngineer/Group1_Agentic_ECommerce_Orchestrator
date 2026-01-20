# Agentic E-Commerce Orchestrator
**Team:** By Harsh Chavva, Matthew Doer, Iyanda Oritola & Koshik Mahapatra

---

## Executive Summary

An agentic AI system that transforms static e-commerce data into a **secure, interactive support workflow**. The system goes beyond traditional RAG by combining multi-source reasoning, fraud detection, and **Human-in-the-Loop (HITL)** controls to safely handle high-stakes actions such as refunds.

---

## Project Goals

* Enable intelligent customer support using structured and unstructured data
* Enforce security and identity verification for sensitive requests
* Detect fraud and risk signals before executing financial actions
* Balance autonomy with mandatory human approval

---

## Key Design Principle

> *Safe autonomy*: the agent can reason, recommend, and draft actions, but the **execution is always gated** by verification, risk assessment, and human approval.

---

## High-Level Architecture

* **Agent Framework:** LangGraph / LangChain
* **Observability & Demo:** LangSmith Studio
* **Structured Data:** Snowflake (Gold Zone)
* **Unstructured Data:** Pinecone (Policy Index)

The agent operates as a **stateful graph** with hard security gates, tool-based reasoning, and conditional routing into human review.

---

## Core Features

### 1. Multi-Source Reasoning Engine

The agent evaluates refund and support requests by reasoning across:

* **Snowflake Gold Tables**: Orders, transactions, user profiles, refund history
* **Pinecone Policy Index**: Return and refund policy clauses by item category

Both tools are accessed through **Pydantic-validated schemas**, ensuring strict input/output contracts between the agent and data layer.

---

### 2. HITL Security & Identity Verification

Any request involving **Personally Identifiable Information (PII) or financial actions** triggers a mandatory security node:

* Execution pauses
* User identity is verified via a human or external check
* Agent state must be updated before proceeding

This makes identity verification a **non-bypassable step** in the workflow.

---

### 3. Red Flag & Fraud Detection

Before processing high-risk actions, the agent evaluates fraud signals derived from policy and historical data:

* **Distance Discrepancy**: Shipping address vs. session/login metadata
* **Refund Velocity**: Excessive refund frequency (more than 3 per month)
* **Chargeback Risk**: Existing or pending chargebacks

Any triggered rule automatically routes the request into human review.

---

## Optional Value-Add Features

### 4. Behavioral Risk Scoring

A composite **Trust Score** is calculated from detected red flags:

* High trust -> Fast-track refund drafting
* Low trust -> Mandatory manual review

---

### 5. Multi-Channel Response Drafting

The agent can generate **reviewable draft responses** (message or email), including:

* Decision outcome
* Policy justification
* Verification status

A human agent reviews, edits if needed, and approves before sending the generated draft.

---

## Human-in-the-Loop Workflow

1. Agent detects a red flag or high-risk condition
2. State is marked as `requires_human_review`
3. Human reviewer sees:

   * Triggered flags
   * Agent reasoning summary
   * Suggested resolution
4. Human approves or edits
5. Agent executes final action (or mocks it in demo)

---

## Demo Walkthrough (LangSmith)

* Visualize the agent graph and state transitions
* Trigger a refund request to show the **identity verification interrupt**
* Inspect reasoning traces for Snowflake and Pinecone tool calls
* Demonstrate a **Refund Velocity** flag routing to human review

---

## Team Responsibilities

**AI/ML Engineering**

* Agent graph design and state management
* Pydantic tool schemas
* HITL gating and fraud logic
* Reasoning traces and demo

**Data Engineering**

* Snowflake Gold table design and logic
* Policy ingestion and Pinecone indexing
* Data quality, contracts, and thresholds