# JobHunter A2UI Web Interface - Design Specification

**Date:** 2026-05-08  
**Project:** JobHunter Agent UI Visualization  
**Style:** Light Soft (Notion/Airtable inspired)

## Overview

A simple web interface that visualizes the JobHunter agent's workflow using the A2UI protocol principles. The UI will render job search results, resume parsing, and job matching in a clean, card-based layout.

## Design Language

### Color Palette
- **Background:** `#F7F8FA` (soft gray)
- **Surface:** `#FFFFFF` (white cards)
- **Primary:** `#2563EB` (blue)
- **Secondary:** `#7C3AED` (purple accent)
- **Text Primary:** `#1F2937`
- **Text Secondary:** `#6B7280`
- **Success:** `#059669`
- **Border:** `#E5E7EB`

### Typography
- **Font:** Inter (Google Fonts)
- **Headings:** 600 weight
- **Body:** 400 weight
- **Sizes:** 14px base, 18px h2, 24px h1

### Spacing
- **Base unit:** 8px
- **Card padding:** 24px
- **Gap between cards:** 16px
- **Section gaps:** 32px

## Page Structure

```
┌─────────────────────────────────────────────────────────┐
│  Header: "JobHunter Agent" + Status Badge               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Resume Section                                  │   │
│  │  - Input textarea for resume text               │   │
│  │  - "Parse Resume" button                        │   │
│  │  - Parsed skills displayed as tags              │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Job Search Section                              │   │
│  │  - Search input + "Search Jobs" button          │   │
│  │  - Job count indicator                          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Matched Jobs Section                            │   │
│  │  - Job cards with title, company, score, tags   │   │
│  │  - Hover state for interaction                  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Cover Letter Generator                          │   │
│  │  - Select job + "Generate" button               │   │
│  │  - Generated letter displayed                   │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## Component Inventory

### 1. Header
- Logo text "JobHunter" with agent icon
- Status badge: "Ready" / "Processing..."
- Subtle bottom border

### 2. Input Card
- White background, subtle shadow
- Label + textarea (200px height)
- Primary action button
- Loading spinner state

### 3. Job Card
- White background, rounded corners (8px)
- Left accent border (4px, colored by relevance)
- Title (bold), Company (gray), URL link
- Skills tags (small pills)
- Relevance score badge (top right)
- Hover: slight lift shadow

### 4. Skill Tag
- Pill shape, light blue background
- Small text, rounded

### 5. Button
- Primary: blue bg, white text
- Secondary: white bg, gray border
- Loading: spinner + disabled state

### 6. Cover Letter Panel
- Expandable card
- Formatted text display
- Copy button

## Interaction Flow

1. **User enters resume text** → clicks "Parse" → sees extracted skills as tags
2. **User enters job search query** → clicks "Search" → sees job cards appear (staggered animation)
3. **Jobs auto-match** with resume skills → relevance scores calculated
4. **User clicks job card** → can generate cover letter
5. **Cover letter displayed** in panel below

## A2UI-Inspired Data Structure

```javascript
// Surface: main-app
// Components rendered as JSON-driven cards

const appState = {
  resume: {
    text: "",
    parsed: false,
    skills: []
  },
  jobs: {
    query: "",
    searching: false,
    results: [],
    matched: []
  },
  selectedJob: null,
  coverLetter: null
}
```

## Technical Approach

- **Single HTML file** with embedded CSS and JavaScript
- **No framework** - vanilla JS for simplicity
- **CSS Grid** for layout
- **Fetch API** calls to agent tools (simulated locally)
- **Local storage** for session persistence

## Sections Scale

- Header: Simple, static
- Resume Input: Medium complexity (textarea + parsing)
- Job Search: Medium (input + results grid)
- Matched Jobs: Complex (dynamic cards, filtering)
- Cover Letter: Simple (display panel)

## Implementation Order

1. HTML structure with CSS
2. Static layout (no functionality)
3. Add JavaScript for resume parsing display
4. Add job card rendering
5. Add matching visualization
6. Add cover letter section