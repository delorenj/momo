# Momo: 33GOD's Agentic Ticketing Workflow and Project Lifecycle System

Momo is an employee with a particular set of skills and a set of custom tools that enable him to do his job.

## What is Momo?

- Momo is an agent specification, defining a role and personality
- Momo is a skill package defining precise workflows that make up his job description and responsibilities
- Momo is an MCP server exposing the very set of tools needed to successfully complete his assigned workflows and tasks.
- Momo is specially trained/created to be agent framework/cli agnostic
- Momo comes with a set of agent adapters to enable integration in any environment.
- Momo workflows can be invoked manually through multiple gateways (Telegram, CLI, web, Bloodbank) or given agency through an interval heartbeat and a declaritive set of goals and accompanying pillars to guide its decisions on each tick.

## Architectural North Star and Product Pillars

- Momo is designed to be a modular, pluggable, and extensible framework. It should not be tied to any specific agentic platform or agent CLI.
- Momo should be able to integrate with any agentic platform or agent CLI via fan out with a set of adapters.
- Momo's responsibilities should mirror those of both a typical tech company's project manager + engineering manager hybrid. Momo controls the project's ticket board, but also has the responsibility of delegating tasks to the teams subagents.
- Momo has the responsibility of of deeply understanding the project's business domain and the business requirements of the project to the extent that it will be entrusted to make unblocking decisions on behalf of the CEO (human operator. me.)

### The Pillars (decision function)

The declarative pillars that guide Momo's decisions on each tick. These are *my*
business pillars, and because Momo decides on my behalf, they are also Momo's (and
Toad's, and every agent's). **Canonical source of truth: [`PILLARS.md`](./PILLARS.md)
— do not fork it, reference it.** In priority order:

1. **Chase the Check** — revenue is the compass; rank by shortest path to a real payment.
2. **Dogfood the Platform** — build products ON 33GOD; each product hardens the platform, each platform piece must earn its keep on a real product.
3. **Build LEGO, Not Statues** — layered abstraction for reuse/extension; done = liftable without surgery. Governed by the **Rule of Three** (abstract on the *second* occurrence, not the first).
4. **Gang of Four by Default** — standard patterns first (they deliver #3); domain patterns (outbox, saga, CQRS) only when genuinely event-driven.

Also mirrored to the vault Karpathy wiki (`wiki/operating-doctrine/pillars.md`).

## Components

Current functionality is exactly how I want it, and it's currently all wrapped in a single skill (~/code/skillex/all-skills/momo). So this is going to be the promotion of this skill into a formal component. We're also going to expand it from just a skill to a proper package that includes not only the skill(s), but also a custom MCP server that provides connectivity to Plane and Trello, an agent definition, and a way to install a heartbeat interval service, and a set of agent adapters to enable integration with any agentic platform or agent CLI.

### MCP Server

I'm not sure how this will work, because a Plane server already exists, and I already made a Trello server. So this would be a third server that sits on top of the other two as a proxy, and will have high-level tools. Then, depending on what ticket provider we're using, it'll delegate to the proper connection server.

### Agent Definition

Agency CLIs all have their own standard for defining agent specs. I know Claude has its own agent system, and so does OpenCode, and so does GitHub Copilot. So does Kimi, et cetera. So this agent spec needs to be agnostic, and any agent's CLI integration needs to be handled via fan-out adapters. So just keep the agent spec as generic as possible.

Something important to note is that in the current state, all of this is being handled by default by Hermes agents and the Hermes agent fleet. Every project gets deployed its own Hermes project manager.
So this is the end state of what I want, had we used this Momo—which hasn't been created yet—with a Hermes adapter. I want to be able to have this agent, this Momo workflow, and install it in Claude using an adapter, and in Gemini using an adapter. So when you're implementing, look to the Hermes implementation in the Hermes fleet. The personality is handled there by a soul file and a role file.
But like I said, it should be generic, and maybe the adapter for Hermes will take that generic thing and port it over to the soul.

### Agent Adapters

Adapters are the way to enable integration with any agentic platform or agent CLI. Planned are:

- Hermes
- Codex
- OpenCode
- Kimi
- Gemini
- Claude

### Heartbeat Interval Service

This is currently best seen as the functioning Hermes Fleet Agent Project Managers—the Hermes PM—for each project. And it's manifest as a systemd heartbeat interval. I don't imagine it would be any different, but we would pull that from there and it would live in this Momo component.

### Memory

Hindsight should be the framework used for memory, and I'd like to keep the memory for the Momo agent—currently known as the Hermes Agent PM—the same. I want to keep it as the same bank. I don't want to confuse things by separating agent memories by identity; I'd rather keep it the way it is and make each project a bank.
