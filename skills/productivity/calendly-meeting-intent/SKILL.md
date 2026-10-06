---
name: calendly-meeting-intent
description: Pull Calendly booking objectives and tags into a pre-meeting brief.
version: 1.0.0
author: Max Infeld
license: MIT
metadata:
  hermes:
    tags: [Calendly, Meetings, Intent]
    related_skills: [meeting-workflow-setup, readai-signal-extract]
required_environment_variables:
  - name: CALENDLY_TOKEN
    prompt: Calendly personal access token
    help: https://calendly.com/integrations/api_webhooks
    required_for: reading invitee questions and answers
---

# Calendly meeting intent

## When to Use

An `invitee.created` webhook arrived, or the user asks to prep a booked meeting.

## Procedure

1. Load `meeting-workflow-setup` if `CALENDLY_TOKEN` is missing.
2. Read `questions_and_answers[]` (`question`, `answer`, `position`), `tracking` (`utm_campaign`, `utm_source`, `utm_medium`, `utm_content`, `utm_term`), event name, `start_time`, invitee name and email.
3. Map question text containing objective, goal, or agenda to `objective`. Map Tags, product, or area answers, plus `utm_campaign` and event type name, to `tags[]`. Event type name is a tag, not the objective.
4. Write `meetings/<iso-start>__<email-slug>.json` with objective, tags, attendees, event_name, calendly_uri, start_time. Leave objective null if unanswered. Do not invent one.

## Pitfalls

Calendly has no native tags. An empty Tags question stays empty.

## Verification

Brief file exists and every field traces to a payload field.
