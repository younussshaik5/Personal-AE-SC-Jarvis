---
name: data-seeder
description: AI-powered demo data generator with dynamic schema fetching, industry-realistic scenarios, and intelligent validation for YourCompany instances
version: 2.0
author: YourCompany SE Team
last_updated: 2026-03-11
tags:
  - presales
  - demo-data
  - seeding
  - validation
  - freshworks
  - solution-engineering
---
# SKILL: Data Seeder Module (Dynamic Edition)

**Module ID:** `dataSeeder` | **File:** `src/modules/dataSeeder.js`  
**Audience:** YourCompany Solution Engineering (Presales)  
**YourCompany Context:** Demo Instance Population, Trial Setup

---

## Overview

AI-powered demo data generator with dynamic schema fetching, adaptive validation, and intelligent data storytelling. Creates industry-realistic data that matches actual YourCompany instance configurations.

---

## Dynamic Schema Intelligence

### Schema Fetching (NEW)

Before generating data, AI attempts to fetch actual schema:

1. **From Connected Instance**:
   - Call `YourCompanyService.getTicketFields()`
   - Call `YourCompanyService.getContactFields()`
   - Call `YourCompanyService.getCompanyFields()`
   - `[FETCH: Custom fields, required fields, field types]`

2. **Schema Adaptation**:
   - Map generated data to actual field names
   - Identify required vs optional fields
   - `[VALIDATE: Data types match schema]`

3. **Fallback Schema**:
   - If no connection: Use standard YourCompany schema
   - `[FLAG: "Using default schema - connect instance for custom fields"]`

---

## Inputs (Enhanced)

| Field ID | Label | Type | Dynamic Helper |
|----------|-------|------|----------------|
| `seed-industry` | Industry | select | fintech, healthcare, ecommerce, saas, education, manufacturing |
| `seed-type` | Data Type | select | tickets, contacts, companies |
| `seed-count` | Number of Records | select | 5, 10, 25, 50 |
| `seed-scenario` | Custom Scenario | text | `[SUGGEST: Based on industry trends]` |
| `seed-file` | Attachments | file (multi) | Schema examples, JSON templates |

---

## AI Generation (Dynamic)

### Pre-Processing:

```
1. Fetch schema from connected instance (if available)
2. Research industry-specific scenarios (current trends)
3. Identify realistic data patterns for {industry}
4. Generate data matching schema requirements
5. Validate against field types and constraints
```

### Dynamic Schema Requirements:

#### Tickets (Adaptive Schema)

Base fields (always include):
- `subject`, `description`, `priority`, `status`

**Dynamic custom fields** (from schema fetch):
- Map to actual custom field names from instance
- Include realistic values for picklist fields
- `[VALIDATE: Required fields present]`

**Industry-Specific Scenarios** (Research-Enhanced):

- **FinTech**: Regulatory compliance tickets, fraud alerts, PCI issues, refund requests
- **Healthcare**: HIPAA compliance, patient data requests, insurance claims, appointment issues
- **E-commerce**: Order issues, returns, inventory, peak season spikes, Shopify integration
- **SaaS**: Onboarding, feature requests, churn risk, API issues, subscription billing
- **Education**: Student records, LMS issues, enrollment, financial aid, grading
- **Manufacturing**: Supply chain, quality control, warranty claims, logistics

**AI Prompt:**

```
Generate {count} realistic {industry} {type} records.
Industry context: {current_trends_researched}
Scenario: {custom_scenario}
Schema: {fetched_schema or default_schema}

Requirements:
- Multi-paragraph descriptions (3-5 paragraphs)
- Realistic data patterns for {industry}
- Include edge cases and escalations
- Match schema field types exactly
- Valid JSON array only
- Include Freddy AI-relevant data where applicable
```

#### Contacts (Adaptive)

Base fields:
- `name`, `email` (corporate domain), `phone`, `company_id`

**Dynamic fields** (from schema):
- Custom contact fields
- Job titles relevant to {industry}
- Departments typical for {industry}
- Seniority levels (C-level, VP, Director, Manager)

**Research-Enhanced:**
- `[FETCH: Common naming conventions for {industry}]`
- `[FETCH: Typical company structures for {industry}]`

#### Companies (Adaptive)

Base fields:
- `name`, `domains`, `description`, `industry`

**Dynamic fields** (from schema):
- Custom company fields
- Health score logic
- Contract value ranges for {industry}
- Employee count ranges for {industry}

---

## Validation Engine (Enhanced)

### Schema-Aware Validation

```js
validateData(data, type, schema) {
  // Check against actual schema
  required_fields = schema.required_fields
  field_types = schema.field_types

  // Validate each record
  for record in data:
    for field in required_fields:
      if !record[field]: errors.push(`Missing ${field}`)

    // Type validation
    if field_types[field] == 'integer' && !isInt(record[field]):
      errors.push(`${field} should be integer`)

    // Custom validation rules from schema
    if schema.validations[field]:
      apply schema.validations[field]
}
```

### Auto-Fix Engine (Schema-Aware)

**Ticket fixes:**
- Missing required fields → defaults from schema
- Invalid priority/status → valid values from schema picklist
- Short description → append contextually relevant detail

**Contact fixes:**
- Invalid email → generate from name + {industry} domain patterns
- Missing required custom fields → realistic defaults

**Company fixes:**
- Short name → append industry-appropriate suffix
- Missing custom fields → industry-typical values

---

## Preview & Push (Enhanced)

### Preview

- Show formatted JSON
- **NEW**: Show schema mapping: "Field X maps to custom field Y"
- **NEW**: Highlight required fields
- **NEW**: Show validation status per record

### Push to Instance (Schema-Matched)

```js
pushToInstance() {
  // Map generated fields to actual schema fields
  mapped_data = mapToSchema(this.generatedData, this.schema)

  // Validate before push
  validation = validateData(mapped_data, type, schema)
  if !validation.valid: show errors, abort

  // Push with field name mapping
  for record in mapped_data:
    YourCompanyService.create{type}(record, schema_mapping)
}
```

**Rate Limiting:** 200ms between records
**Progress Tracking:** Success/fail per record with field-level error details

---

## Export Actions (Enhanced)

### Copy JSON

- Include schema metadata
- Include generation context (industry, scenario, timestamp)

### Download JSON

- Filename: `seed-data-{industry}-{type}-{count}-{date}.json`
- Include schema mapping document
- Include data dictionary

---

## Key Dynamic Features

1. **Schema Adaptation**: Data matches actual instance configuration
2. **Industry Intelligence**: Scenarios based on current trends
3. **Smart Validation**: Schema-aware, not hardcoded rules
4. **Field Mapping**: Handles custom field names automatically
5. **Realistic Patterns**: Industry-typical data distributions

---

## Dependencies

- `GeminiService` — AI generation
- `YourCompanyService` — Schema fetch + data push
- `WebSearchService` — Industry trends (NEW)
- `window.App.readFile(file)` — Schema templates

---

## Industry Scenarios Reference

### FinTech:
- PCI compliance violations
- Fraud detection alerts
- Refund processing delays
- Account security issues
- Regulatory audit requests

### Healthcare:
- HIPAA compliance tickets
- Patient data access requests
- Insurance verification issues
- Appointment scheduling conflicts
- Medical record discrepancies

### E-commerce:
- Order fulfillment delays
- Return authorization requests
- Inventory sync issues
- Payment processing errors
- Peak season capacity alerts

### SaaS:
- Onboarding assistance
- Feature adoption questions
- API integration support
- Churn risk indicators
- Subscription billing issues
